"""Split Result DTO - Data Transfer Object for operation results"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SplitResult:
    """Result DTO for PDF split operations"""
    success: bool
    output_files: List[str] = field(default_factory=list)
    error_message: Optional[str] = None

    @property
    def file_count(self) -> int:
        """Number of files generated"""
        return len(self.output_files)

    @classmethod
    def create_success(cls, output_files: List[str]) -> 'SplitResult':
        """Create a successful result"""
        return cls(success=True, output_files=output_files)

    @classmethod
    def create_error(cls, error_message: str) -> 'SplitResult':
        """Create an error result"""
        return cls(success=False, error_message=error_message)
