"""Split View Model - Handles split PDF operations"""
from typing import Optional, List
import os
from .base_view_model import BaseViewModel
from application.use_cases.split_pdf_by_ranges import SplitPDFByRangesUseCase
from application.use_cases.split_pdf_by_chapters import SplitPDFByChaptersUseCase
from application.use_cases.split_pdf_each_page import SplitPDFEachPageUseCase
from application.use_cases.preview_split import PreviewSplitUseCase
from application.dtos.split_request import (
    SplitByRangesRequest,
    SplitByChaptersRequest,
    SplitEachPageRequest
)
from application.dtos.preview_result import PreviewResult


class SplitViewModel(BaseViewModel):
    """
    View Model for PDF split operations

    Events:
    - split_started: Fired when split operation starts
    - split_progress: Fired with progress updates (progress: int)
    - split_completed: Fired when split completes (success: bool, message: str, files: List[str])
    - preview_updated: Fired when preview is updated (preview: PreviewResult)
    """

    def __init__(
        self,
        split_by_ranges_use_case: SplitPDFByRangesUseCase,
        split_by_chapters_use_case: SplitPDFByChaptersUseCase,
        split_each_page_use_case: SplitPDFEachPageUseCase,
        preview_use_case: PreviewSplitUseCase
    ):
        super().__init__()
        self._split_by_ranges = split_by_ranges_use_case
        self._split_by_chapters = split_by_chapters_use_case
        self._split_each_page = split_each_page_use_case
        self._preview = preview_use_case

        # Properties
        self._input_file: str = ""
        self._output_dir: str = ""
        self._ranges: str = ""
        self._template: str = "{name}_{start}-{end}.pdf"
        self._total_pages: int = 0
        self._is_busy: bool = False

    @property
    def input_file(self) -> str:
        return self._input_file

    @input_file.setter
    def input_file(self, value: str):
        self._input_file = value
        self._notify_property_changed("input_file", value)

        # Auto-set output directory
        if value and not self._output_dir:
            self.output_dir = os.path.dirname(value)

    @property
    def output_dir(self) -> str:
        return self._output_dir

    @output_dir.setter
    def output_dir(self, value: str):
        self._output_dir = value
        self._notify_property_changed("output_dir", value)

    @property
    def ranges(self) -> str:
        return self._ranges

    @ranges.setter
    def ranges(self, value: str):
        self._ranges = value
        self._notify_property_changed("ranges", value)

    @property
    def template(self) -> str:
        return self._template

    @template.setter
    def template(self, value: str):
        self._template = value
        self._notify_property_changed("template", value)

    @property
    def total_pages(self) -> int:
        return self._total_pages

    @total_pages.setter
    def total_pages(self, value: int):
        self._total_pages = value
        self._notify_property_changed("total_pages", value)

    @property
    def is_busy(self) -> bool:
        return self._is_busy

    @is_busy.setter
    def is_busy(self, value: bool):
        self._is_busy = value
        self._notify_property_changed("is_busy", value)

    def split_by_ranges(self) -> None:
        """Execute split by ranges operation"""
        if not self._validate_input():
            return

        self.is_busy = True
        self._raise_event("split_started")

        # Parse ranges
        range_strings = [r.strip() for r in self._ranges.replace('，', ',').split(',') if r.strip()]

        # Create request
        request = SplitByRangesRequest(
            input_path=self._input_file,
            output_dir=self._output_dir,
            range_strings=range_strings,
            template=self._template,
            progress_callback=self._on_progress
        )

        # Execute use case
        result = self._split_by_ranges.execute(request)

        self.is_busy = False

        if result.success:
            self._raise_event("split_completed", True, f"成功生成 {result.file_count} 个文件", result.output_files)
        else:
            self._raise_event("split_completed", False, result.error_message, [])

    def split_by_chapters(self) -> None:
        """Execute split by chapters operation"""
        if not self._validate_input():
            return

        self.is_busy = True
        self._raise_event("split_started")

        # Create request
        request = SplitByChaptersRequest(
            input_path=self._input_file,
            output_dir=self._output_dir,
            template=self._template,
            progress_callback=self._on_progress
        )

        # Execute use case
        result = self._split_by_chapters.execute(request)

        self.is_busy = False

        if result.success:
            self._raise_event("split_completed", True, f"成功生成 {result.file_count} 个文件", result.output_files)
        else:
            self._raise_event("split_completed", False, result.error_message, [])

    def split_each_page(self) -> None:
        """Execute split each page operation"""
        if not self._validate_input():
            return

        self.is_busy = True
        self._raise_event("split_started")

        # Create request
        request = SplitEachPageRequest(
            input_path=self._input_file,
            output_dir=self._output_dir,
            template="{name}_page_{index}.pdf",
            progress_callback=self._on_progress
        )

        # Execute use case
        result = self._split_each_page.execute(request)

        self.is_busy = False

        if result.success:
            self._raise_event("split_completed", True, f"成功生成 {result.file_count} 个文件", result.output_files)
        else:
            self._raise_event("split_completed", False, result.error_message, [])

    def preview_split(self) -> None:
        """Preview split operation"""
        if not self._input_file:
            return

        # Parse ranges
        range_strings = [r.strip() for r in self._ranges.replace('，', ',').split(',') if r.strip()]

        # Create request
        request = SplitByRangesRequest(
            input_path=self._input_file,
            output_dir=self._output_dir,
            range_strings=range_strings,
            template=self._template
        )

        # Execute preview
        preview_result = self._preview.preview_by_ranges(request)
        self._raise_event("preview_updated", preview_result)

    def _validate_input(self) -> bool:
        """Validate input before split"""
        if not self._input_file:
            self._raise_event("split_completed", False, "请选择输入文件", [])
            return False

        if not self._output_dir:
            self._raise_event("split_completed", False, "请选择输出目录", [])
            return False

        return True

    def _on_progress(self, progress: int) -> None:
        """Progress callback"""
        self._raise_event("split_progress", progress)
