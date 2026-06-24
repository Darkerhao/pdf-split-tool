"""Python 库 EPUB 转换适配器"""
from typing import Callable

from domain.services.epub_service import IEPUBConverter
from domain.models.epub_document import EPUBDocument, PaperSize
from shared.exceptions.domain_exceptions import ConversionFailedError


# 尝试导入 EPUB 相关库
try:
    from ebooklib import epub
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4, A5, letter, legal
    import html2text

    EPUB_LIBS_AVAILABLE = True
except ImportError:
    EPUB_LIBS_AVAILABLE = False


class PythonEPUBAdapter(IEPUBConverter):
    """使用 Python 库（ebooklib + reportlab）实现的 EPUB 转换器

    注意：这是一个简化实现，功能不如 Calibre 完善
    """

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
            ConversionFailedError: 转换失败
        """
        if not self.is_available():
            raise ConversionFailedError("Python EPUB 库不可用，请安装: pip install ebooklib reportlab html2text")

        if progress_callback:
            progress_callback(0.0, "使用 Python 库转换 EPUB")

        try:
            # 读取 EPUB
            book = epub.read_epub(document.path)

            # 获取纸张尺寸
            page_size = self._get_page_size(paper_size)

            # 创建 PDF
            pdf = canvas.Canvas(output_path, pagesize=page_size)

            # 提取文本内容
            h = html2text.HTML2Text()
            h.ignore_links = False

            items = list(book.get_items_of_type(9))  # ITEM_DOCUMENT = 9
            total_items = len(items)

            for index, item in enumerate(items):
                # 解码内容
                try:
                    content = item.get_content().decode('utf-8')
                except Exception:
                    continue

                # 转换为纯文本
                text = h.handle(content)

                # 简单分页写入（这是一个非常简化的实现）
                y = 750
                for line in text.split('\n'):
                    if y < 50:
                        pdf.showPage()
                        y = 750

                    pdf.drawString(50, y, line[:100])  # 限制每行长度
                    y -= 15

                # 报告进度
                if progress_callback:
                    progress = ((index + 1) / total_items) * 100
                    progress_callback(progress, f"处理中: {index + 1}/{total_items}")

            pdf.save()

            if progress_callback:
                progress_callback(100.0, "转换完成！")

            return output_path

        except Exception as e:
            raise ConversionFailedError(f"Python 库转换失败: {str(e)}") from e

    def is_available(self) -> bool:
        """检查转换器是否可用

        Returns:
            True 如果所需库已安装
        """
        return EPUB_LIBS_AVAILABLE

    def get_name(self) -> str:
        """获取转换器名称

        Returns:
            "Python"
        """
        return "Python"

    @staticmethod
    def _get_page_size(paper_size: PaperSize):
        """获取 reportlab 页面尺寸"""
        size_map = {
            PaperSize.A4: A4,
            PaperSize.A5: A5,
            PaperSize.LETTER: letter,
            PaperSize.LEGAL: legal
        }
        return size_map.get(paper_size, A4)


class CompositeEPUBConverter(IEPUBConverter):
    """组合 EPUB 转换器

    尝试使用 Python 库，失败后回退到 Calibre
    """

    def __init__(self):
        self._python_converter = PythonEPUBAdapter()
        self._calibre_converter = None  # 延迟导入

    def convert(
        self,
        document: EPUBDocument,
        output_path: str,
        paper_size: PaperSize = PaperSize.A4,
        progress_callback: Callable[[float, str], None] = None
    ) -> str:
        """将 EPUB 转换为 PDF

        优先使用 Python 库，失败后使用 Calibre
        """
        # 尝试 Python 库
        if self._python_converter.is_available():
            try:
                return self._python_converter.convert(
                    document, output_path, paper_size, progress_callback
                )
            except Exception:
                # Python 库失败，尝试 Calibre
                pass

        # 回退到 Calibre
        if self._calibre_converter is None:
            from .calibre_adapter import CalibreAdapter
            self._calibre_converter = CalibreAdapter()

        if self._calibre_converter.is_available():
            return self._calibre_converter.convert(
                document, output_path, paper_size, progress_callback
            )

        raise ConversionFailedError(
            "EPUB 转换失败：Python 库和 Calibre 均不可用。"
            "请安装: pip install ebooklib reportlab html2text 或安装 Calibre"
        )

    def is_available(self) -> bool:
        """检查至少一个转换器可用"""
        if self._python_converter.is_available():
            return True

        if self._calibre_converter is None:
            from .calibre_adapter import CalibreAdapter
            self._calibre_converter = CalibreAdapter()

        return self._calibre_converter.is_available()

    def get_name(self) -> str:
        """获取当前使用的转换器名称"""
        if self._python_converter.is_available():
            return "Python (with Calibre fallback)"
        return "Calibre"
