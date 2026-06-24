"""EPUB 转换领域服务接口"""
from abc import ABC, abstractmethod
from typing import Callable
from ..models.epub_document import EPUBDocument, PaperSize


class IEPUBConverter(ABC):
    """EPUB 转 PDF 服务接口"""

    @abstractmethod
    def convert(
        self,
        document: EPUBDocument,
        output_path: str,
        paper_size: PaperSize = PaperSize.A4,
        progress_callback: Callable[[float, str], None] = None
    ) -> str:
        """将 EPUB 转换为 PDF

        Args:
            document: EPUB 文档对象
            output_path: 输出 PDF 文件路径
            paper_size: 纸张大小
            progress_callback: 进度回调函数

        Returns:
            输出文件路径

        Raises:
            ValueError: 文件格式无效
            IOError: 文件读写错误
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查转换器是否可用

        Returns:
            True 如果转换器可用
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """获取转换器名称（如 "Calibre", "Python"）

        Returns:
            转换器名称
        """
        pass
