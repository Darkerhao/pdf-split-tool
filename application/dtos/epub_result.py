"""EPUB Conversion Result DTO"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ConvertEPUBResult:
    """Result DTO for EPUB to PDF conversion"""
    success: bool
    output_path: Optional[str] = None
    error_message: Optional[str] = None

    @classmethod
    def create_success(cls, output_path: str) -> 'ConvertEPUBResult':
        """Create a successful result"""
        return cls(success=True, output_path=output_path)

    @classmethod
    def create_error(cls, error_message: str) -> 'ConvertEPUBResult':
        """Create an error result"""
        return cls(success=False, error_message=error_message)
