"""Preview Split Use Case"""
from typing import List
from domain.models.page_range import PageRange
from domain.repositories.document_repository import IDocumentRepository
from application.dtos.split_request import SplitByRangesRequest, SplitByChaptersRequest
from application.dtos.preview_result import PreviewResult, PreviewItem
from shared.exceptions.domain_exceptions import DocumentNotFoundError, InvalidDocumentFormatError
import os


class PreviewSplitUseCase:
    """Use case for previewing split operation before execution"""

    def __init__(self, document_repository: IDocumentRepository):
        self._document_repo = document_repository

    def preview_by_ranges(self, request: SplitByRangesRequest) -> PreviewResult:
        """
        Preview split by ranges operation

        Args:
            request: SplitByRangesRequest containing input path, ranges, and template

        Returns:
            PreviewResult with preview items
        """
        try:
            # Load document
            document = self._document_repo.load(request.input_path)

            # Parse ranges
            ranges = self._parse_ranges(request.range_strings)

            # Generate preview items
            items = []
            base_name = os.path.splitext(os.path.basename(request.input_path))[0]

            for idx, page_range in enumerate(ranges, start=1):
                if not document.validate_range(page_range):
                    continue

                filename = self._render_filename(
                    template=request.template,
                    name=base_name,
                    start=page_range.start,
                    end=page_range.end,
                    index=idx
                )

                items.append(PreviewItem(
                    output_filename=filename,
                    page_range_str=f"{page_range.start}-{page_range.end}",
                    page_count=page_range.page_count
                ))

            return PreviewResult(items=items, total_files=len(items))

        except (DocumentNotFoundError, InvalidDocumentFormatError):
            return PreviewResult(items=[], total_files=0)

    def preview_by_chapters(self, request: SplitByChaptersRequest) -> PreviewResult:
        """
        Preview split by chapters operation

        Args:
            request: SplitByChaptersRequest containing input path and template

        Returns:
            PreviewResult with preview items
        """
        try:
            # Load document
            document = self._document_repo.load(request.input_path)

            if not document.chapters:
                return PreviewResult(items=[], total_files=0)

            # Generate preview items
            items = []
            base_name = os.path.splitext(os.path.basename(request.input_path))[0]

            for idx, chapter in enumerate(document.chapters, start=1):
                filename = self._render_filename(
                    template=request.template,
                    name=base_name,
                    start=chapter.start_page,
                    end=chapter.end_page,
                    index=idx,
                    chapter_title=chapter.title
                )

                items.append(PreviewItem(
                    output_filename=filename,
                    page_range_str=f"{chapter.start_page}-{chapter.end_page}",
                    page_count=chapter.page_count
                ))

            return PreviewResult(items=items, total_files=len(items))

        except (DocumentNotFoundError, InvalidDocumentFormatError):
            return PreviewResult(items=[], total_files=0)

    def _parse_ranges(self, range_strings: List[str]) -> List[PageRange]:
        """Parse string representations into PageRange objects"""
        ranges = []
        for range_str in range_strings:
            try:
                page_range = PageRange.parse(range_str.strip())
                ranges.append(page_range)
            except ValueError:
                pass
        return ranges

    def _render_filename(self, template: str, **kwargs) -> str:
        """
        Render filename template with variables

        Supported variables: {name}, {start}, {end}, {index}, {chapter_title}
        """
        filename = template
        for key, value in kwargs.items():
            placeholder = f"{{{key}}}"
            if placeholder in filename:
                # Clean chapter title (remove invalid characters)
                if key == "chapter_title":
                    value = self._clean_filename(str(value))
                filename = filename.replace(placeholder, str(value))
        return filename

    def _clean_filename(self, filename: str) -> str:
        """Remove invalid characters from filename"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename
