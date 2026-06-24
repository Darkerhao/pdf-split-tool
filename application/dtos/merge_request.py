"""Merge Request DTO - Data Transfer Object for PDF merging operations"""
from dataclasses import dataclass
from typing import List, Optional, Callable


@dataclass
class MergePDFsRequest:
    """Request DTO for merging multiple PDFs"""
    input_paths: List[str]
    output_path: str
    progress_callback: Optional[Callable[[int], None]] = None
