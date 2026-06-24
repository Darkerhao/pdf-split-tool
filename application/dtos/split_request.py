"""Split Request DTO - Data Transfer Object for PDF splitting operations"""
from dataclasses import dataclass
from typing import List, Optional, Callable


@dataclass
class SplitByRangesRequest:
    """Request DTO for splitting PDF by page ranges"""
    input_path: str
    output_dir: str
    range_strings: List[str]
    template: str = "{name}_{start}-{end}.pdf"
    progress_callback: Optional[Callable[[int], None]] = None


@dataclass
class SplitByChaptersRequest:
    """Request DTO for splitting PDF by chapters"""
    input_path: str
    output_dir: str
    template: str = "{name}_{index}_{chapter_title}.pdf"
    progress_callback: Optional[Callable[[int], None]] = None


@dataclass
class SplitEachPageRequest:
    """Request DTO for splitting PDF into individual pages"""
    input_path: str
    output_dir: str
    template: str = "{name}_page_{index}.pdf"
    progress_callback: Optional[Callable[[int], None]] = None
