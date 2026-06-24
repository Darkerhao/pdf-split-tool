"""PDF 拆分领域服务接口"""
from abc import ABC, abstractmethod
from typing import List, Callable
from ..models.pdf_document import PDFDocument
from ..models.page_range import PageRange


class ProgressCallback:
    """进度回调协议"""
    def __call__(self, progress: float, message: str) -> None:
        """报告进度

        Args:
            progress: 进度百分比（0-100）
            message: 进度消息
        """
        pass


class IPDFSplitter(ABC):
    """PDF 拆分服务接口

    领域服务：封装不属于某个实体或值对象的业务逻辑
    """

    @abstractmethod
    def split_by_ranges(
        self,
        document: PDFDocument,
        ranges: List[PageRange],
        output_template: str,
        progress_callback: Callable[[float, str], None] = None
    ) -> List[str]:
        """按页码范围拆分 PDF

        Args:
            document: PDF 文档对象
            ranges: 页码范围列表
            output_template: 输出文件名模板（支持 {name}, {start}, {end}, {index}）
            progress_callback: 进度回调函数

        Returns:
            生成的文件路径列表

        Raises:
            ValueError: 范围无效
            IOError: 文件读写错误
        """
        pass

    @abstractmethod
    def split_into_single_pages(
        self,
        document: PDFDocument,
        output_template: str,
        progress_callback: Callable[[float, str], None] = None
    ) -> List[str]:
        """将 PDF 拆分为单页

        Args:
            document: PDF 文档对象
            output_template: 输出文件名模板
            progress_callback: 进度回调函数

        Returns:
            生成的文件路径列表
        """
        pass

    @abstractmethod
    def split_by_chapters(
        self,
        document: PDFDocument,
        output_template: str,
        progress_callback: Callable[[float, str], None] = None
    ) -> List[str]:
        """按章节拆分 PDF

        Args:
            document: PDF 文档对象（必须包含章节信息）
            output_template: 输出文件名模板
            progress_callback: 进度回调函数

        Returns:
            生成的文件路径列表

        Raises:
            ValueError: 文档不包含章节信息
        """
        pass


class IPDFMerger(ABC):
    """PDF 合并服务接口"""

    @abstractmethod
    def merge(
        self,
        document_paths: List[str],
        output_path: str,
        progress_callback: Callable[[float, str], None] = None
    ) -> str:
        """合并多个 PDF 文件

        Args:
            document_paths: 要合并的 PDF 文件路径列表
            output_path: 输出文件路径
            progress_callback: 进度回调函数

        Returns:
            输出文件路径

        Raises:
            ValueError: 文件列表为空
            FileNotFoundError: 某个文件不存在
            IOError: 文件读写错误
        """
        pass
