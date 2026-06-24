"""PDF 拆分服务实现"""
import os
from typing import List, Callable
from PyPDF2 import PdfReader, PdfWriter

from domain.services.pdf_service import IPDFSplitter, IPDFMerger
from domain.models.pdf_document import PDFDocument
from domain.models.page_range import PageRange
from shared.exceptions.domain_exceptions import InvalidPageRangeError, ChaptersNotFoundError


def sanitize_filename(name: str) -> str:
    """清理文件名，移除非法字符"""
    bad = '\\/:*?"<>|'
    for ch in bad:
        name = name.replace(ch, '_')
    return name


def render_template(base_name: str, start: int, end: int, index: int, template: str) -> str:
    """渲染文件名模板

    Args:
        base_name: 基础文件名（不含扩展名）
        start: 起始页码
        end: 结束页码
        index: 文件索引（从 1 开始）
        template: 模板字符串（支持 {name}, {start}, {end}, {index}）

    Returns:
        渲染后的文件名
    """
    if not template:
        template = "{name}_{start}-{end}.pdf"

    try:
        filename = template.format(name=base_name, start=start, end=end, index=index)
    except Exception:
        # 模板格式错误时使用默认格式
        filename = f"{base_name}_{start}-{end}.pdf"

    return sanitize_filename(filename)


class PyPDFSplitter(IPDFSplitter):
    """使用 PyPDF2 实现的 PDF 拆分服务"""

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
            output_template: 输出文件名模板
            progress_callback: 进度回调函数

        Returns:
            生成的文件路径列表
        """
        if not ranges:
            raise InvalidPageRangeError("页码范围列表不能为空")

        # 规范化范围
        normalized_ranges = document.normalize_ranges(ranges)
        if not normalized_ranges:
            raise InvalidPageRangeError("没有有效的页码范围")

        # 计算总工作量
        total_pages = sum(r.page_count for r in normalized_ranges)
        completed_pages = 0

        # 报告初始进度
        if progress_callback:
            progress_callback(0.0, "开始拆分 PDF")

        # 读取 PDF
        reader = PdfReader(document.path)

        # 解析输出路径
        base_dir = os.path.dirname(output_template) or os.getcwd()
        base_name = os.path.splitext(os.path.basename(output_template))[0]

        # 拆分每个范围
        output_files: List[str] = []

        for index, page_range in enumerate(normalized_ranges, start=1):
            # 生成输出文件名
            output_filename = render_template(
                base_name,
                page_range.start,
                page_range.end,
                index,
                output_template
            )
            output_path = os.path.join(base_dir, output_filename)

            # 创建 PDF 写入器
            writer = PdfWriter()

            # 添加页面（PyPDF2 页码从 0 开始）
            for page_num in range(page_range.start - 1, page_range.end):
                writer.add_page(reader.pages[page_num])
                completed_pages += 1

                # 报告进度
                if progress_callback:
                    progress = (completed_pages / total_pages) * 100
                    progress_callback(progress, f"正在处理第 {completed_pages}/{total_pages} 页")

            # 写入文件
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)

            output_files.append(output_path)

        # 完成
        if progress_callback:
            progress_callback(100.0, f"完成！已生成 {len(output_files)} 个文件")

        return output_files

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
        if progress_callback:
            progress_callback(0.0, "开始拆分为单页")

        reader = PdfReader(document.path)
        base_dir = os.path.dirname(output_template) or os.getcwd()
        base_name = os.path.splitext(os.path.basename(output_template))[0]

        output_files: List[str] = []

        for page_num in range(1, document.total_pages + 1):
            # 生成输出文件名
            output_filename = render_template(
                base_name,
                page_num,
                page_num,
                page_num,
                output_template
            )
            output_path = os.path.join(base_dir, output_filename)

            # 创建单页 PDF
            writer = PdfWriter()
            writer.add_page(reader.pages[page_num - 1])

            # 写入文件
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)

            output_files.append(output_path)

            # 报告进度
            if progress_callback:
                progress = (page_num / document.total_pages) * 100
                progress_callback(progress, f"正在处理第 {page_num}/{document.total_pages} 页")

        if progress_callback:
            progress_callback(100.0, f"完成！已生成 {len(output_files)} 个文件")

        return output_files

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
        """
        if not document.has_chapters():
            raise ChaptersNotFoundError("文档不包含章节信息")

        if progress_callback:
            progress_callback(0.0, "开始按章节拆分")

        # 将章节转换为页码范围
        ranges = [ch.page_range for ch in document.chapters]

        # 使用 split_by_ranges 实现
        return self.split_by_ranges(document, ranges, output_template, progress_callback)


class PyPDFMerger(IPDFMerger):
    """使用 PyPDF2 实现的 PDF 合并服务"""

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
        """
        if not document_paths:
            raise ValueError("文件列表不能为空")

        if progress_callback:
            progress_callback(0.0, "开始合并 PDF")

        writer = PdfWriter()
        total_files = len(document_paths)

        for index, path in enumerate(document_paths, start=1):
            # 检查文件是否存在
            if not os.path.exists(path):
                raise FileNotFoundError(f"文件不存在: {path}")

            # 读取并添加页面
            reader = PdfReader(path)
            for page in reader.pages:
                writer.add_page(page)

            # 报告进度
            if progress_callback:
                progress = (index / total_files) * 100
                progress_callback(progress, f"正在合并第 {index}/{total_files} 个文件")

        # 写入输出文件
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)

        if progress_callback:
            progress_callback(100.0, "合并完成！")

        return output_path
