"""领域仓储接口（抽象层）

仓储模式：封装数据访问逻辑，提供类似集合的接口来访问领域对象。
遵循依赖倒置原则：领域层定义接口，基础设施层实现接口。
"""
from abc import ABC, abstractmethod
from typing import Optional
from ..models.pdf_document import PDFDocument
from ..models.epub_document import EPUBDocument


class IDocumentRepository(ABC):
    """文档仓储接口

    负责 PDF 和 EPUB 文档的加载和保存
    """

    @abstractmethod
    def load_pdf(self, path: str) -> PDFDocument:
        """加载 PDF 文档

        Args:
            path: 文件路径

        Returns:
            PDFDocument 对象

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式无效
        """
        pass

    @abstractmethod
    def load_epub(self, path: str) -> EPUBDocument:
        """加载 EPUB 文档

        Args:
            path: 文件路径

        Returns:
            EPUBDocument 对象

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式无效
        """
        pass

    @abstractmethod
    def get_pdf_metadata(self, path: str) -> dict:
        """获取 PDF 元数据（标题、作者等）

        Args:
            path: 文件路径

        Returns:
            元数据字典
        """
        pass
