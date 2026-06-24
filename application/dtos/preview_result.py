"""Preview Result DTO - Data Transfer Object for preview operations"""
from dataclasses import dataclass
from typing import List


@dataclass
class PreviewItem:
    """Preview item for a single output file"""
    output_filename: str
    page_range_str: str
    page_count: int


@dataclass
class PreviewResult:
    """Result DTO for split preview operations"""
    items: List[PreviewItem]
    total_files: int

    @property
    def is_empty(self) -> bool:
        """Check if preview is empty"""
        return len(self.items) == 0
