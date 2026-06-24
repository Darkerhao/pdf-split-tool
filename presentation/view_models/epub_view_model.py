"""EPUB View Model - Handles EPUB to PDF conversion"""
from .base_view_model import BaseViewModel
from application.use_cases.convert_epub import ConvertEPUBUseCase
from application.dtos.epub_request import ConvertEPUBRequest


class EPUBViewModel(BaseViewModel):
    """
    View Model for EPUB to PDF conversion

    Events:
    - conversion_started: Fired when conversion starts
    - conversion_progress: Fired with progress updates (progress: int)
    - conversion_completed: Fired when conversion completes (success: bool, message: str, output_path: str)
    """

    def __init__(self, convert_use_case: ConvertEPUBUseCase):
        super().__init__()
        self._convert_use_case = convert_use_case

        # Properties
        self._input_file: str = ""
        self._output_file: str = ""
        self._paper_size: str = "a4"
        self._is_busy: bool = False

    @property
    def input_file(self) -> str:
        return self._input_file

    @input_file.setter
    def input_file(self, value: str):
        self._input_file = value
        self._notify_property_changed("input_file", value)

    @property
    def output_file(self) -> str:
        return self._output_file

    @output_file.setter
    def output_file(self, value: str):
        self._output_file = value
        self._notify_property_changed("output_file", value)

    @property
    def paper_size(self) -> str:
        return self._paper_size

    @paper_size.setter
    def paper_size(self, value: str):
        self._paper_size = value
        self._notify_property_changed("paper_size", value)

    @property
    def is_busy(self) -> bool:
        return self._is_busy

    @is_busy.setter
    def is_busy(self, value: bool):
        self._is_busy = value
        self._notify_property_changed("is_busy", value)

    def convert(self) -> None:
        """Execute EPUB to PDF conversion"""
        if not self._validate_input():
            return

        self.is_busy = True
        self._raise_event("conversion_started")

        # Create request
        request = ConvertEPUBRequest(
            input_path=self._input_file,
            output_path=self._output_file,
            progress_callback=self._on_progress
        )

        # Execute use case
        result = self._convert_use_case.execute(request)

        self.is_busy = False

        if result.success:
            self._raise_event("conversion_completed", True, "转换成功", result.output_path)
        else:
            self._raise_event("conversion_completed", False, result.error_message, "")

    def _validate_input(self) -> bool:
        """Validate input before conversion"""
        if not self._input_file:
            self._raise_event("conversion_completed", False, "请选择输入文件", "")
            return False

        if not self._output_file:
            self._raise_event("conversion_completed", False, "请选择输出文件", "")
            return False

        return True

    def _on_progress(self, progress: int) -> None:
        """Progress callback"""
        self._raise_event("conversion_progress", progress)
