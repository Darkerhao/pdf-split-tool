"""Unit tests for Split PDF by Ranges Use Case"""
import unittest
from unittest.mock import Mock, MagicMock
from domain.models.pdf_document import PDFDocument
from domain.models.page_range import PageRange
from domain.repositories.document_repository import IDocumentRepository
from domain.services.pdf_service import IPDFSplitter
from application.use_cases.split_pdf_by_ranges import SplitPDFByRangesUseCase
from application.dtos.split_request import SplitByRangesRequest
from shared.exceptions.domain_exceptions import DocumentNotFoundError


class TestSplitPDFByRangesUseCase(unittest.TestCase):
    """Test cases for SplitPDFByRangesUseCase"""

    def setUp(self):
        """Set up test fixtures"""
        self.document_repo = Mock(spec=IDocumentRepository)
        # Configure the mock to have the load method
        self.document_repo.load = Mock()
        self.pdf_splitter = Mock(spec=IPDFSplitter)
        self.use_case = SplitPDFByRangesUseCase(self.document_repo, self.pdf_splitter)

    def test_execute_success(self):
        """Test successful split by ranges"""
        # Arrange
        document = PDFDocument(path="test.pdf", total_pages=10)
        self.document_repo.load.return_value = document
        self.pdf_splitter.split_by_ranges.return_value = ["output1.pdf", "output2.pdf"]

        request = SplitByRangesRequest(
            input_path="test.pdf",
            output_dir="output",
            range_strings=["1-3", "5-7"],
            template="{name}_{start}-{end}.pdf"
        )

        # Act
        result = self.use_case.execute(request)

        # Assert
        self.assertTrue(result.success)
        self.assertEqual(len(result.output_files), 2)
        self.assertIsNone(result.error_message)
        self.document_repo.load.assert_called_once_with("test.pdf")
        self.pdf_splitter.split_by_ranges.assert_called_once()

    def test_execute_document_not_found(self):
        """Test split when document is not found"""
        # Arrange
        self.document_repo.load.side_effect = DocumentNotFoundError("File not found")
        request = SplitByRangesRequest(
            input_path="missing.pdf",
            output_dir="output",
            range_strings=["1-3"],
            template="{name}_{start}-{end}.pdf"
        )

        # Act
        result = self.use_case.execute(request)

        # Assert
        self.assertFalse(result.success)
        self.assertEqual(len(result.output_files), 0)
        self.assertIn("Document not found", result.error_message)

    def test_execute_invalid_ranges(self):
        """Test split with invalid page ranges"""
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
        result = self.use_case.execute(request)

        # Assert
        self.assertFalse(result.success)
        self.assertIn("No valid page ranges", result.error_message)

    def test_execute_mixed_valid_invalid_ranges(self):
        """Test split with mixed valid and invalid ranges"""
        # Arrange
        document = PDFDocument(path="test.pdf", total_pages=10)
        self.document_repo.load.return_value = document
        self.pdf_splitter.split_by_ranges.return_value = ["output1.pdf"]

        request = SplitByRangesRequest(
            input_path="test.pdf",
            output_dir="output",
            range_strings=["1-3", "15-20", "5-7"],  # Middle one is invalid
            template="{name}_{start}-{end}.pdf"
        )

        # Act
        result = self.use_case.execute(request)

        # Assert
        self.assertTrue(result.success)
        # Should only process valid ranges
        call_args = self.pdf_splitter.split_by_ranges.call_args
        ranges = call_args[1]['ranges']
        self.assertEqual(len(ranges), 2)  # Only 2 valid ranges

    def test_parse_ranges_with_single_pages(self):
        """Test parsing ranges including single pages"""
        # Arrange
        document = PDFDocument(path="test.pdf", total_pages=10)
        self.document_repo.load.return_value = document
        self.pdf_splitter.split_by_ranges.return_value = ["output1.pdf", "output2.pdf"]

        request = SplitByRangesRequest(
            input_path="test.pdf",
            output_dir="output",
            range_strings=["1", "3-5", "7"],  # Mix of single pages and ranges
            template="{name}_{start}-{end}.pdf"
        )

        # Act
        result = self.use_case.execute(request)

        # Assert
        self.assertTrue(result.success)
        call_args = self.pdf_splitter.split_by_ranges.call_args
        ranges = call_args[1]['ranges']
        self.assertEqual(len(ranges), 3)

    def test_parse_ranges_with_whitespace(self):
        """Test parsing ranges with extra whitespace"""
        # Arrange
        document = PDFDocument(path="test.pdf", total_pages=10)
        self.document_repo.load.return_value = document
        self.pdf_splitter.split_by_ranges.return_value = ["output.pdf"]

        request = SplitByRangesRequest(
            input_path="test.pdf",
            output_dir="output",
            range_strings=["  1-3  ", " 5-7 "],  # Extra whitespace
            template="{name}_{start}-{end}.pdf"
        )

        # Act
        result = self.use_case.execute(request)

        # Assert
        self.assertTrue(result.success)

    def test_execute_with_progress_callback(self):
        """Test split with progress callback"""
        # Arrange
        document = PDFDocument(path="test.pdf", total_pages=10)
        self.document_repo.load.return_value = document
        self.pdf_splitter.split_by_ranges.return_value = ["output.pdf"]

        progress_callback = Mock()
        request = SplitByRangesRequest(
            input_path="test.pdf",
            output_dir="output",
            range_strings=["1-5"],
            template="{name}_{start}-{end}.pdf",
            progress_callback=progress_callback
        )

        # Act
        result = self.use_case.execute(request)

        # Assert
        self.assertTrue(result.success)
        # Check that progress callback was passed to splitter
        call_args = self.pdf_splitter.split_by_ranges.call_args
        self.assertEqual(call_args[1]['progress_callback'], progress_callback)


if __name__ == '__main__':
    unittest.main()
