"""Split PDF by Chapters Use Case"""
from domain.repositories.document_repository import IDocumentRepository
from domain.services.pdf_service import IPDFSplitter
from application.dtos.split_request import SplitByChaptersRequest
from application.dtos.split_result import SplitResult
from shared.exceptions.domain_exceptions import DocumentNotFoundError, InvalidDocumentFormatError


class SplitPDFByChaptersUseCase:
    """Use case for splitting PDF by chapters (bookmarks/outline)"""

    def __init__(
        self,
        document_repository: IDocumentRepository,
        pdf_splitter: IPDFSplitter
    ):
        self._document_repo = document_repository
        self._pdf_splitter = pdf_splitter

    def execute(self, request: SplitByChaptersRequest) -> SplitResult:
        """
        Execute the split by chapters use case

        Args:
            request: SplitByChaptersRequest containing input path, output dir, and template

        Returns:
            SplitResult with success status and output files or error message
        """
        try:
            # 1. Load document
            document = self._document_repo.load(request.input_path)

            # 2. Check if document has chapters
            if not document.chapters:
                return SplitResult.create_error("Document has no chapters/bookmarks")

            # 3. Build output template path (dir + template)
            import os
            output_template = os.path.join(request.output_dir, request.template)

            # 4. Split by chapters
            output_files = self._pdf_splitter.split_by_chapters(
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
