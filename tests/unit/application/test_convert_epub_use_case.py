"""Unit tests for Convert EPUB Use Case"""
import unittest
from unittest.mock import Mock
from domain.services.epub_service import IEPUBConverter
from application.use_cases.convert_epub import ConvertEPUBUseCase
from application.dtos.epub_request import ConvertEPUBRequest
from shared.exceptions.domain_exceptions import DocumentNotFoundError, InvalidDocumentFormatError


class TestConvertEPUBUseCase(unittest.TestCase):
    """Test cases for ConvertEPUBUseCase"""

    def setUp(self):
        """Set up test fixtures"""
        self.epub_converter = Mock(spec=IEPUBConverter)
        self.use_case = ConvertEPUBUseCase(self.epub_converter)

    def test_execute_success(self):
        """Test successful EPUB conversion"""
        # Arrange
        self.epub_converter.is_available.return_value = True
        request = ConvertEPUBRequest(
            input_path="book.epub",
            output_path="book.pdf"
        )

        # Act
        result = self.use_case.execute(request)

        # Assert
        self.assertTrue(result.success)
        self.assertEqual(result.output_path, "book.pdf")
        self.assertIsNone(result.error_message)
        self.epub_converter.convert.assert_called_once()

    def test_execute_converter_not_available(self):
        """Test conversion when converter is not available"""
        # Arrange
        self.epub_converter.is_available.return_value = False
        request = ConvertEPUBRequest(
            input_path="book.epub",
            output_path="book.pdf"
        )

        # Act
        result = self.use_case.execute(request)

        # Assert
        self.assertFalse(result.success)
        self.assertIn("not available", result.error_message)
        self.epub_converter.convert.assert_not_called()

    def test_execute_document_not_found(self):
        """Test conversion when document is not found"""
        # Arrange
        self.epub_converter.is_available.return_value = True
        self.epub_converter.convert.side_effect = DocumentNotFoundError("File not found")
        request = ConvertEPUBRequest(
            input_path="missing.epub",
            output_path="book.pdf"
        )

        # Act
        result = self.use_case.execute(request)

        # Assert
        self.assertFalse(result.success)
        self.assertIn("Document not found", result.error_message)

    def test_execute_invalid_format(self):
        """Test conversion with invalid document format"""
        # Arrange
        self.epub_converter.is_available.return_value = True
        self.epub_converter.convert.side_effect = InvalidDocumentFormatError("Not an EPUB file")
        request = ConvertEPUBRequest(
            input_path="book.txt",
            output_path="book.pdf"
        )

        # Act
        result = self.use_case.execute(request)

        # Assert
        self.assertFalse(result.success)
        self.assertIn("Invalid document format", result.error_message)

    def test_execute_with_progress_callback(self):
        """Test conversion with progress callback"""
        # Arrange
        self.epub_converter.is_available.return_value = True
        progress_callback = Mock()
        request = ConvertEPUBRequest(
            input_path="book.epub",
            output_path="book.pdf",
            progress_callback=progress_callback
        )

        # Act
        result = self.use_case.execute(request)

        # Assert
        self.assertTrue(result.success)
        call_args = self.epub_converter.convert.call_args
        self.assertEqual(call_args[1]['progress_callback'], progress_callback)


if __name__ == '__main__':
    unittest.main()
