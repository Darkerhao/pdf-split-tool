"""EPUB Conversion Request DTO"""
from dataclasses import dataclass
from typing import Optional, Callable


@dataclass
class ConvertEPUBRequest:
    """Request DTO for EPUB to PDF conversion"""
    input_path: str
    output_path: str
    progress_callback: Optional[Callable[[int], None]] = None
