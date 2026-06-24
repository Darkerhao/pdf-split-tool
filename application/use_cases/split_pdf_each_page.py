"""Split PDF into Individual Pages Use Case"""
from domain.repositories.document_repository import IDocumentRepository
from domain.services.pdf_service import IPDFSplitter
from application.dtos.split_request import SplitEachPageRequest
from application.dtos.split_result import SplitResult
from shared.exceptions.domain_exceptions import DocumentNotFoundError, InvalidDocumentFormatError


class SplitPDFEachPageUseCase:
    """Use case for splitting PDF into individual pages"""

    def __init__(
        self,
        document_repository: IDocumentRepository,
        pdf_splitter: IPDFSplitter
    ):
        self._document_repo = document_repository
        self._pdf_splitter = pdf_splitter

    def execute(self, request: SplitEachPageRequest) -> SplitResult:
        """
        Execute the split each page use case

        Args:
            request: SplitEachPageRequest containing input path, output dir, and template

        Returns:
            SplitResult with success status and output files or error message
        """
        try:
            # 1. Load document
            document = self._document_repo.load(request.input_path)

            # 2. Build output template path (dir + template)
            import os
            output_template = os.path.join(request.output_dir, request.template)

            # 3. Split into individual pages
            output_files = self._pdf_splitter.split_into_single_pages(
                document=document,
                output_template=output_template,
                progress_callback=request.progress_callback
            )

            return SplitResult.create_success(output_files)

        except DocumentNotFoundError as e:
            return SplitResult.create_error(f"Document not found: {e}")
        except InvalidDocumentFormatError as e:
            return SplitResult.create_error(f"Invalid document format: {e}")
        except Exception as e:
            return SplitResult.create_error(f"Unexpected error: {e}")
