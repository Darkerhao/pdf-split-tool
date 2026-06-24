"""Split PDF by Ranges Use Case"""
from typing import List
from domain.models.page_range import PageRange
from domain.repositories.document_repository import IDocumentRepository
from domain.services.pdf_service import IPDFSplitter
from application.dtos.split_request import SplitByRangesRequest
from application.dtos.split_result import SplitResult
from shared.exceptions.domain_exceptions import DocumentNotFoundError, InvalidDocumentFormatError


class SplitPDFByRangesUseCase:
    """Use case for splitting PDF by page ranges"""

    def __init__(
        self,
        document_repository: IDocumentRepository,
        pdf_splitter: IPDFSplitter
    ):
        self._document_repo = document_repository
        self._pdf_splitter = pdf_splitter

    def execute(self, request: SplitByRangesRequest) -> SplitResult:
        """
        Execute the split by ranges use case

        Args:
            request: SplitByRangesRequest containing input path, output dir, ranges, and template

        Returns:
            SplitResult with success status and output files or error message
        """
        try:
            # 1. Load document
            document = self._document_repo.load(request.input_path)

            # 2. Parse page ranges
            ranges = self._parse_ranges(request.range_strings)

            # 3. Validate ranges
            valid_ranges = [r for r in ranges if document.validate_range(r)]
            if not valid_ranges:
                return SplitResult.create_error("No valid page ranges provided")

            # 4. Build output template path (dir + template)
            import os
            output_template = os.path.join(request.output_dir, request.template)

            # 5. Split PDF
            output_files = self._pdf_splitter.split_by_ranges(
                document=document,
                ranges=valid_ranges,
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

    def _parse_ranges(self, range_strings: List[str]) -> List[PageRange]:
        """Parse string representations into PageRange objects"""
        ranges = []
        for range_str in range_strings:
            try:
                page_range = PageRange.parse(range_str.strip())
                ranges.append(page_range)
            except ValueError:
                # Skip invalid ranges silently
                pass
        return ranges
