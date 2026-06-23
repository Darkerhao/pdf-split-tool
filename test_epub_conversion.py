import os
import tempfile
import unittest
from unittest import mock

from services import epub_service
from task_context import TaskContext


class RecordingTaskContext:
    def __init__(self):
        self.progress_events: list[tuple[float, str]] = []
        self.done_events: list[tuple[str, object]] = []
        self.error_events: list[str] = []
        self.cancel_requested = False
        self.task_context = TaskContext(
            is_cancelled=lambda: self.cancel_requested,
            report_progress=self.record_progress,
            report_done=self.record_done,
            report_error=self.record_error,
        )

    def record_progress(self, pct: float, text: str) -> None:
        self.progress_events.append((pct, text))

    def record_done(self, message: str, payload) -> None:
        self.done_events.append((message, payload))

    def record_error(self, message: str) -> None:
        self.error_events.append(message)


class EpubServiceSmokeTests(unittest.TestCase):
    def create_temp_path(self, suffix: str) -> str:
        handle = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        handle.close()
        self.addCleanup(self.remove_file, handle.name)
        return handle.name

    @staticmethod
    def remove_file(file_path: str) -> None:
        if os.path.exists(file_path):
            os.unlink(file_path)

    def test_epub_libs_available_flag_is_boolean(self):
        self.assertIsInstance(epub_service.EPUB_LIBS_AVAILABLE, bool)

    def test_do_epub_convert_with_progress_uses_task_context_contract(self):
        recorder = RecordingTaskContext()
        epub_path = self.create_temp_path(".epub")
        pdf_path = self.create_temp_path(".pdf")

        def fake_python_backend(ctx, actual_epub_path, actual_pdf_path, paper_size):
            self.assertIs(ctx, recorder.task_context)
            self.assertEqual(actual_epub_path, epub_path)
            self.assertEqual(actual_pdf_path, pdf_path)
            self.assertEqual(paper_size, "a4")
            ctx.report_progress(55, "python backend ok")
            ctx.report_done("python backend done", [actual_pdf_path])

        with mock.patch(
            "services.epub_service.epub_to_pdf_python",
            side_effect=fake_python_backend,
        ):
            result = epub_service.do_epub_convert_with_progress(
                recorder.task_context,
                epub_path,
                pdf_path,
                "a4",
            )

        self.assertEqual(result, "success")
        self.assertFalse(recorder.error_events)
        self.assertGreaterEqual(len(recorder.progress_events), 2)
        self.assertEqual(recorder.progress_events[0][0], 10)
        self.assertEqual(recorder.progress_events[-1], (55, "python backend ok"))
        self.assertTrue(recorder.done_events)
        self.assertEqual(recorder.done_events[-1][1], [pdf_path])

    def test_do_epub_convert_with_progress_reports_error_without_backends(self):
        recorder = RecordingTaskContext()

        with mock.patch(
            "services.epub_service.epub_to_pdf_python",
            side_effect=RuntimeError("python backend failed"),
        ), mock.patch(
            "services.epub_service.find_ebook_convert",
            return_value="",
        ):
            epub_service.do_epub_convert_with_progress(
                recorder.task_context,
                "sample.epub",
                "sample.pdf",
                "a4",
            )

        self.assertFalse(recorder.done_events)
        self.assertEqual(len(recorder.error_events), 1)
        self.assertIn("python backend failed", recorder.error_events[0])


if __name__ == "__main__":
    unittest.main()
