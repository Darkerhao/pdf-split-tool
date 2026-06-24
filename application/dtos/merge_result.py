"""Merge Result DTO - Data Transfer Object for merge operation results"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class MergeResult:
    """Result DTO for PDF merge operations"""
    success: bool
    output_path: Optional[str] = None
    error_message: Optional[str] = None

    @classmethod
    def create_success(cls, output_path: str) -> 'MergeResult':
        """Create a successful result"""
        return cls(success=True, output_path=output_path)

    @classmethod
    def create_error(cls, error_message: str) -> 'MergeResult':
        """Create an error result"""
        return cls(success=False, error_message=error_message)
