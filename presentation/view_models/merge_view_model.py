"""Merge View Model - Handles merge PDF operations"""
from typing import List
from .base_view_model import BaseViewModel
from application.use_cases.merge_pdfs import MergePDFsUseCase
from application.dtos.merge_request import MergePDFsRequest


class MergeViewModel(BaseViewModel):
    """
    View Model for PDF merge operations

    Events:
    - merge_started: Fired when merge operation starts
    - merge_progress: Fired with progress updates (progress: int)
    - merge_completed: Fired when merge completes (success: bool, message: str, output_path: str)
    """

    def __init__(self, merge_use_case: MergePDFsUseCase):
        super().__init__()
        self._merge_use_case = merge_use_case

        # Properties
        self._input_files: List[str] = []
        self._output_file: str = ""
        self._is_busy: bool = False

    @property
    def input_files(self) -> List[str]:
        return self._input_files

    @input_files.setter
    def input_files(self, value: List[str]):
        self._input_files = value
        self._notify_property_changed("input_files", value)

    @property
    def output_file(self) -> str:
        return self._output_file

    @output_file.setter
    def output_file(self, value: str):
        self._output_file = value
        self._notify_property_changed("output_file", value)

    @property
    def is_busy(self) -> bool:
        return self._is_busy

    @is_busy.setter
    def is_busy(self, value: bool):
        self._is_busy = value
        self._notify_property_changed("is_busy", value)

    def add_file(self, file_path: str) -> None:
        """Add a file to merge list"""
        if file_path and file_path not in self._input_files:
            self._input_files.append(file_path)
            self._notify_property_changed("input_files", self._input_files)

    def remove_file(self, file_path: str) -> None:
        """Remove a file from merge list"""
        if file_path in self._input_files:
            self._input_files.remove(file_path)
            self._notify_property_changed("input_files", self._input_files)

    def clear_files(self) -> None:
        """Clear all files"""
        self._input_files.clear()
        self._notify_property_changed("input_files", self._input_files)

    def move_up(self, file_path: str) -> None:
        """Move file up in the list"""
        try:
            index = self._input_files.index(file_path)
            if index > 0:
                self._input_files[index], self._input_files[index - 1] = \
                    self._input_files[index - 1], self._input_files[index]
                self._notify_property_changed("input_files", self._input_files)
        except ValueError:
            pass

    def move_down(self, file_path: str) -> None:
        """Move file down in the list"""
        try:
            index = self._input_files.index(file_path)
            if index < len(self._input_files) - 1:
                self._input_files[index], self._input_files[index + 1] = \
                    self._input_files[index + 1], self._input_files[index]
                self._notify_property_changed("input_files", self._input_files)
        except ValueError:
            pass

    def merge(self) -> None:
        """Execute merge operation"""
        if not self._validate_input():
            return

        self.is_busy = True
        self._raise_event("merge_started")

        # Create request
        request = MergePDFsRequest(
            input_paths=self._input_files,
            output_path=self._output_file,
            progress_callback=self._on_progress
        )

        # Execute use case
        result = self._merge_use_case.execute(request)

        self.is_busy = False

        if result.success:
            self._raise_event("merge_completed", True, "合并成功", result.output_path)
        else:
            self._raise_event("merge_completed", False, result.error_message, "")

    def _validate_input(self) -> bool:
        """Validate input before merge"""
        if len(self._input_files) < 2:
            self._raise_event("merge_completed", False, "请至少选择 2 个文件", "")
            return False

        if not self._output_file:
            self._raise_event("merge_completed", False, "请选择输出文件", "")
            return False

        return True

    def _on_progress(self, progress: int) -> None:
        """Progress callback"""
        self._raise_event("merge_progress", progress)
