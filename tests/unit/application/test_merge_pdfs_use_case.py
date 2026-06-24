"""Unit tests for Merge PDFs Use Case"""
import unittest
from unittest.mock import Mock
from domain.services.pdf_service import IPDFMerger
from application.use_cases.merge_pdfs import MergePDFsUseCase
from application.dtos.merge_request import MergePDFsRequest
from shared.exceptions.domain_exceptions import DocumentNotFoundError


class TestMergePDFsUseCase(unittest.TestCase):
    """Test cases for MergePDFsUseCase"""

    def setUp(self):
        """Set up test fixtures"""
        self.pdf_merger = Mock(spec=IPDFMerger)
        self.use_case = MergePDFsUseCase(self.pdf_merger)

    def test_execute_success(self):
        """Test successful merge"""
        # Arrange
        request = MergePDFsRequest(
            input_paths=["file1.pdf", "file2.pdf", "file3.pdf"],
            output_path="merged.pdf"
        )

        # Act
        result = self.use_case.execute(request)

        # Assert
        self.assertTrue(result.success)
        self.assertEqual(result.output_path, "merged.pdf")
        self.assertIsNone(result.error_message)
        self.pdf_merger.merge.assert_called_once()

    def test_execute_no_input_files(self):
        """Test merge with no input files"""
        # Arrange
        request = MergePDFsRequest(
            input_paths=[],
            output_path="merged.pdf"
        )

        # Act
        result = self.use_case.execute(request)

        # Assert
        self.assertFalse(result.success)
        self.assertIn("No input files", result.error_message)
        self.pdf_merger.merge.assert_not_called()

    def test_execute_single_input_file(self):
        """Test merge with only one input file"""
        # Arrange
        request = MergePDFsRequest(
            input_paths=["file1.pdf"],
            output_path="merged.pdf"
        )

        # Act
        result = self.use_case.execute(request)

        # Assert
        self.assertFalse(result.success)
        self.assertIn("At least 2 PDF files", result.error_message)
        self.pdf_merger.merge.assert_not_called()

    def test_execute_document_not_found(self):
        """Test merge when a document is not found"""
        # Arrange
        self.pdf_merger.merge.side_effect = DocumentNotFoundError("File not found")
        request = MergePDFsRequest(
            input_paths=["file1.pdf", "missing.pdf"],
            output_path="merged.pdf"
        )

        # Act
        result = self.use_case.execute(request)

        # Assert
        self.assertFalse(result.success)
        self.assertIn("Document not found", result.error_message)

    def test_execute_with_progress_callback(self):
        """Test merge with progress callback"""
        # Arrange
        progress_callback = Mock()
        request = MergePDFsRequest(
            input_paths=["file1.pdf", "file2.pdf"],
            output_path="merged.pdf",
            progress_callback=progress_callback
        )

        # Act
        result = self.use_case.execute(request)

        # Assert
        self.assertTrue(result.success)
        call_args = self.pdf_merger.merge.call_args
        self.assertEqual(call_args[1]['progress_callback'], progress_callback)


if __name__ == '__main__':
    unittest.main()
