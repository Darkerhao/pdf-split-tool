import os
import tempfile
import unittest

from PyPDF2 import PdfWriter

from services.pdf_service import (
    build_split_preview,
    normalize_page_ranges,
    parse_chapter_ranges,
    parse_ranges,
    render_template,
    sanitize_filename,
)


class PdfServiceSmokeTests(unittest.TestCase):
    def create_temp_pdf(self, page_count: int) -> str:
        handle = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        handle.close()
        self.addCleanup(self.remove_file, handle.name)

        writer = PdfWriter()
        for _ in range(page_count):
            writer.add_blank_page(width=72, height=72)

        with open(handle.name, "wb") as file:
            writer.write(file)

        return handle.name

    @staticmethod
    def remove_file(file_path: str) -> None:
        if os.path.exists(file_path):
            os.unlink(file_path)

    def test_parse_ranges_keeps_valid_items_and_skips_invalid_items(self):
        self.assertEqual(parse_ranges("1-3,5,7-9,abc"), [(1, 3), (5, 5), (7, 9)])

    def test_normalize_page_ranges_clamps_to_document_bounds(self):
        self.assertEqual(
            normalize_page_ranges([(3, 1), (0, 2), (9, 12), (11, 15)], 10),
            [(1, 3), (1, 2), (9, 10)],
        )

    def test_build_split_preview_reports_valid_and_invalid_ranges(self):
        pdf_path = self.create_temp_pdf(page_count=5)

        preview = build_split_preview(pdf_path, "1-2,4,8-9")

        self.assertEqual(preview.valid_count, 2)
        self.assertEqual(len(preview.lines), 3)
        self.assertIn("1-2", preview.lines[0])
        self.assertIn("4-4", preview.lines[1])
        self.assertIn("8-9", preview.lines[2])

    def test_build_split_preview_rejects_empty_ranges(self):
        pdf_path = self.create_temp_pdf(page_count=2)

        with self.assertRaises(ValueError):
            build_split_preview(pdf_path, "")

    def test_parse_chapter_ranges_accepts_multiline_input(self):
        self.assertEqual(parse_chapter_ranges("1-3\n5-7"), [(1, 3), (5, 7)])

    def test_parse_chapter_ranges_rejects_invalid_lines(self):
        with self.assertRaises(ValueError):
            parse_chapter_ranges("1-3\n第二章")

    def test_render_template_falls_back_and_sanitizes_filename(self):
        self.assertEqual(
            render_template("book", 1, 3, 2, "{name}:chapter<{index}>.pdf"),
            "book_chapter_2_.pdf",
        )
        self.assertEqual(sanitize_filename("a:b*c?.pdf"), "a_b_c_.pdf")


if __name__ == "__main__":
    unittest.main()
