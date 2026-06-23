import unittest

import split_pdf_gui
from services import epub_service, pdf_service


EXPECTED_EXPORTS = {
    "EPUB_LIBS_AVAILABLE",
    "batch_epub_to_pdf",
    "build_split_preview",
    "do_epub_convert_with_progress",
    "epub_to_pdf_python",
    "main",
    "normalize_page_ranges",
    "parse_chapter_ranges",
    "parse_ranges",
    "render_template",
    "sanitize_filename",
}


class SplitPdfGuiPublicApiTests(unittest.TestCase):
    def test_public_exports_match_current_module_boundary(self):
        self.assertEqual(set(split_pdf_gui.__all__), EXPECTED_EXPORTS)

        for export_name in EXPECTED_EXPORTS:
            self.assertTrue(
                hasattr(split_pdf_gui, export_name),
                msg=f"缺少导出符号: {export_name}",
            )

    def test_pdf_service_bindings_point_to_current_implementations(self):
        self.assertIs(split_pdf_gui.build_split_preview, pdf_service.build_split_preview)
        self.assertIs(split_pdf_gui.normalize_page_ranges, pdf_service.normalize_page_ranges)
        self.assertIs(split_pdf_gui.parse_chapter_ranges, pdf_service.parse_chapter_ranges)
        self.assertIs(split_pdf_gui.parse_ranges, pdf_service.parse_ranges)
        self.assertIs(split_pdf_gui.render_template, pdf_service.render_template)
        self.assertIs(split_pdf_gui.sanitize_filename, pdf_service.sanitize_filename)

    def test_epub_service_bindings_point_to_current_implementations(self):
        self.assertIs(split_pdf_gui.EPUB_LIBS_AVAILABLE, epub_service.EPUB_LIBS_AVAILABLE)
        self.assertIs(split_pdf_gui.batch_epub_to_pdf, epub_service.batch_epub_to_pdf)
        self.assertIs(
            split_pdf_gui.do_epub_convert_with_progress,
            epub_service.do_epub_convert_with_progress,
        )
        self.assertIs(split_pdf_gui.epub_to_pdf_python, epub_service.epub_to_pdf_python)

    def test_main_entrypoint_remains_callable(self):
        self.assertTrue(callable(split_pdf_gui.main))


if __name__ == "__main__":
    unittest.main()
