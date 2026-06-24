"""EPUB 文档领域模型"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class PaperSize(Enum):
    """纸张大小枚举"""
    A4 = "a4"
    A5 = "a5"
    LETTER = "letter"
    LEGAL = "legal"

    @classmethod
    def from_string(cls, value: str) -> 'PaperSize':
        """从字符串解析纸张大小"""
        normalized = value.lower().strip()
        for paper in cls:
            if paper.value == normalized:
                return paper
        return cls.A4  # 默认 A4


@dataclass
class EPUBDocument:
    """EPUB 文档领域模型"""
    path: str
    title: Optional[str] = None
    author: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        """验证文档路径"""
        if not self.path.lower().endswith('.epub'):
            raise ValueError(f"文件必须是 .epub 格式: {self.path}")
