"""Merge PDFs Use Case"""
from domain.services.pdf_service import IPDFMerger
from application.dtos.merge_request import MergePDFsRequest
from application.dtos.merge_result import MergeResult
from shared.exceptions.domain_exceptions import DocumentNotFoundError, InvalidDocumentFormatError


class MergePDFsUseCase:
    """Use case for merging multiple PDFs into one"""

    def __init__(self, pdf_merger: IPDFMerger):
        self._pdf_merger = pdf_merger

    def execute(self, request: MergePDFsRequest) -> MergeResult:
        """
        Execute the merge PDFs use case

        Args:
            request: MergePDFsRequest containing input paths and output path

        Returns:
            MergeResult with success status and output path or error message
        """
        try:
            # Validate input paths
            if not request.input_paths:
                return MergeResult.create_error("No input files provided")

            if len(request.input_paths) < 2:
                return MergeResult.create_error("At least 2 PDF files are required for merging")

            # Merge PDFs
            self._pdf_merger.merge(
                document_paths=request.input_paths,
                output_path=request.output_path,
                progress_callback=request.progress_callback
            )

            return MergeResult.create_success(request.output_path)

        except DocumentNotFoundError as e:
            return MergeResult.create_error(f"Document not found: {e}")
        except InvalidDocumentFormatError as e:
            return MergeResult.create_error(f"Invalid document format: {e}")
        except Exception as e:
            return MergeResult.create_error(f"Unexpected error: {e}")
