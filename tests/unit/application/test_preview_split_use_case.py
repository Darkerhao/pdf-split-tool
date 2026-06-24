"""Unit tests for Preview Split Use Case"""
import unittest
from unittest.mock import Mock
from domain.models.pdf_document import PDFDocument
from domain.models.chapter import Chapter
from domain.repositories.document_repository import IDocumentRepository
from application.use_cases.preview_split import PreviewSplitUseCase
from application.dtos.split_request import SplitByRangesRequest, SplitByChaptersRequest
from shared.exceptions.domain_exceptions import DocumentNotFoundError


class TestPreviewSplitUseCase(unittest.TestCase):
    """Test cases for PreviewSplitUseCase"""

    def setUp(self):
        """Set up test fixtures"""
        self.document_repo = Mock(spec=IDocumentRepository)
        # Configure the mock to have the load method
        self.document_repo.load = Mock()
        self.use_case = PreviewSplitUseCase(self.document_repo)

    def test_preview_by_ranges_success(self):
        """Test successful preview by ranges"""
        # Arrange
        document = PDFDocument(path="test.pdf", total_pages=10)
        self.document_repo.load.return_value = document

        request = SplitByRangesRequest(
            input_path="test.pdf",
            output_dir="output",
            range_strings=["1-3", "5-7"],
            template="{name}_{start}-{end}.pdf"
        )

        # Act
        result = self.use_case.preview_by_ranges(request)

        # Assert
        self.assertEqual(len(result.items), 2)
        self.assertEqual(result.total_files, 2)
        self.assertFalse(result.is_empty)
        self.assertEqual(result.items[0].output_filename, "test_1-3.pdf")
        self.assertEqual(result.items[0].page_range_str, "1-3")
        self.assertEqual(result.items[0].page_count, 3)

    def test_preview_by_ranges_invalid_ranges(self):
        """Test preview with invalid ranges"""
        # Arrange
        document = PDFDocument(path="test.pdf", total_pages=10)
        self.document_repo.load.return_value = document

        request = SplitByRangesRequest(
            input_path="test.pdf",
            output_dir="output",
            range_strings=["15-20", "25-30"],  # Out of bounds
            template="{name}_{start}-{end}.pdf"
        )

        # Act
        result = self.use_case.preview_by_ranges(request)

        # Assert
        self.assertEqual(len(result.items), 0)
        self.assertTrue(result.is_empty)

    def test_preview_by_ranges_document_not_found(self):
        """Test preview when document is not found"""
        # Arrange
        self.document_repo.load.side_effect = DocumentNotFoundError("File not found")

        request = SplitByRangesRequest(
            input_path="missing.pdf",
            output_dir="output",
            range_strings=["1-3"],
            template="{name}_{start}-{end}.pdf"
        )

        # Act
        result = self.use_case.preview_by_ranges(request)

        # Assert
        self.assertEqual(len(result.items), 0)
        self.assertTrue(result.is_empty)

    def test_preview_by_chapters_success(self):
        """Test successful preview by chapters"""
        # Arrange
        document = PDFDocument(
            path="test.pdf",
            total_pages=20,
            chapters=[
                Chapter(title="Chapter 1", start_page=1, end_page=5),
                Chapter(title="Chapter 2", start_page=6, end_page=10)
            ]
        )
        self.document_repo.load.return_value = document

        request = SplitByChaptersRequest(
            input_path="test.pdf",
            output_dir="output",
            template="{name}_{index}_{chapter_title}.pdf"
        )

        # Act
        result = self.use_case.preview_by_chapters(request)

        # Assert
        self.assertEqual(len(result.items), 2)
        self.assertEqual(result.total_files, 2)
        self.assertEqual(result.items[0].output_filename, "test_1_Chapter 1.pdf")
        self.assertEqual(result.items[0].page_range_str, "1-5")
        self.assertEqual(result.items[0].page_count, 5)

    def test_preview_by_chapters_no_chapters(self):
        """Test preview when document has no chapters"""
        # Arrange
        document = PDFDocument(path="test.pdf", total_pages=10)
        self.document_repo.load.return_value = document

        request = SplitByChaptersRequest(
            input_path="test.pdf",
            output_dir="output",
            template="{name}_{index}_{chapter_title}.pdf"
        )

        # Act
        result = self.use_case.preview_by_chapters(request)

        # Assert
        self.assertEqual(len(result.items), 0)
        self.assertTrue(result.is_empty)

    def test_clean_filename_removes_invalid_chars(self):
        """Test that invalid characters are removed from filenames"""
        # Arrange
        document = PDFDocument(
            path="test.pdf",
            total_pages=10,
            chapters=[
                Chapter(title="Chapter: 1/2", start_page=1, end_page=5)
            ]
        )
        self.document_repo.load.return_value = document

        request = SplitByChaptersRequest(
            input_path="test.pdf",
            output_dir="output",
            template="{chapter_title}.pdf"
        )

        # Act
        result = self.use_case.preview_by_chapters(request)

        # Assert
        self.assertEqual(len(result.items), 1)
        # Colons and slashes should be replaced with underscores
        self.assertEqual(result.items[0].output_filename, "Chapter_ 1_2.pdf")


if __name__ == '__main__':
    unittest.main()
