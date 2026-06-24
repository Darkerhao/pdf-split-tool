"""Convert EPUB to PDF Use Case"""
from domain.services.epub_service import IEPUBConverter
from domain.models.epub_document import EPUBDocument, PaperSize
from application.dtos.epub_request import ConvertEPUBRequest
from application.dtos.epub_result import ConvertEPUBResult
from shared.exceptions.domain_exceptions import DocumentNotFoundError, InvalidDocumentFormatError


class ConvertEPUBUseCase:
    """Use case for converting EPUB to PDF"""

    def __init__(self, epub_converter: IEPUBConverter):
        self._epub_converter = epub_converter

    def execute(self, request: ConvertEPUBRequest) -> ConvertEPUBResult:
        """
        Execute the EPUB to PDF conversion use case

        Args:
            request: ConvertEPUBRequest containing input path, output path, and progress callback

        Returns:
            ConvertEPUBResult with success status and output path or error message
        """
        try:
            # Check converter availability
            if not self._epub_converter.is_available():
                return ConvertEPUBResult.create_error(
                    "EPUB converter is not available. Please install required dependencies."
                )

            # Create EPUB document object (may raise ValueError if not .epub)
            try:
                document = EPUBDocument(path=request.input_path)
            except ValueError as e:
                # Convert ValueError to InvalidDocumentFormatError
                raise InvalidDocumentFormatError(str(e))

            # Convert EPUB to PDF
            self._epub_converter.convert(
                document=document,
                output_path=request.output_path,
                paper_size=PaperSize.A4,
                progress_callback=request.progress_callback
            )

            return ConvertEPUBResult.create_success(request.output_path)

        except DocumentNotFoundError as e:
            return ConvertEPUBResult.create_error(f"Document not found: {e}")
        except InvalidDocumentFormatError as e:
            return ConvertEPUBResult.create_error(f"Invalid document format: {e}")
        except Exception as e:
            return ConvertEPUBResult.create_error(f"Unexpected error: {e}")
