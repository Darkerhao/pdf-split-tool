"""PyPDF2 文档仓储实现"""
from typing import Optional
from PyPDF2 import PdfReader

from domain.repositories.document_repository import IDocumentRepository
from domain.models.pdf_document import PDFDocument, Chapter
from domain.models.epub_document import EPUBDocument
from shared.exceptions.domain_exceptions import (
    DocumentNotFoundError,
    InvalidDocumentFormatError
)


class PyPDFRepository(IDocumentRepository):
    """使用 PyPDF2 实现的文档仓储"""

    def load_pdf(self, path: str) -> PDFDocument:
        """加载 PDF 文档

        Args:
            path: 文件路径

        Returns:
            PDFDocument 对象

        Raises:
            DocumentNotFoundError: 文件不存在
            InvalidDocumentFormatError: 文件格式无效
        """
        try:
            reader = PdfReader(path)
            total_pages = len(reader.pages)

            # 尝试提取章节信息（通过书签/大纲）
            chapters = self._extract_chapters(reader)

            # 提取元数据
            metadata = self._extract_metadata(reader)

            return PDFDocument(
                path=path,
                total_pages=total_pages,
                chapters=chapters,
                metadata=metadata
            )
        except FileNotFoundError as e:
            raise DocumentNotFoundError(f"文档未找到: {path}") from e
        except Exception as e:
            raise InvalidDocumentFormatError(f"无效的 PDF 格式: {path}") from e

    def load_epub(self, path: str) -> EPUBDocument:
        """加载 EPUB 文档

        Args:
            path: 文件路径

        Returns:
            EPUBDocument 对象

        Raises:
            DocumentNotFoundError: 文件不存在
            InvalidDocumentFormatError: 文件格式无效
        """
        try:
            # 简单验证文件存在
            import os
            if not os.path.exists(path):
                raise DocumentNotFoundError(f"文档未找到: {path}")

            # 创建基本的 EPUB 文档对象
            # 元数据提取可以后续通过 ebooklib 实现
            return EPUBDocument(path=path)
        except DocumentNotFoundError:
            raise
        except Exception as e:
            raise InvalidDocumentFormatError(f"无效的 EPUB 格式: {path}") from e

    def get_pdf_metadata(self, path: str) -> dict:
        """获取 PDF 元数据

        Args:
            path: 文件路径

        Returns:
            元数据字典
        """
        try:
            reader = PdfReader(path)
            return self._extract_metadata(reader)
        except Exception:
            return {}

    def _extract_chapters(self, reader: PdfReader) -> list:
        """从 PDF 书签/大纲提取章节信息

        Args:
            reader: PdfReader 对象

        Returns:
            章节列表
        """
        chapters = []

        try:
            outlines = reader.outline
            if not outlines:
                return chapters

            # 递归提取书签
            def extract_outline(outline_items, level=0):
                for item in outline_items:
                    if isinstance(item, list):
                        # 嵌套书签
                        extract_outline(item, level + 1)
                    else:
                        # 单个书签
                        try:
                            title = str(item.title) if hasattr(item, 'title') else "未命名章节"
                            page_obj = item.page if hasattr(item, 'page') else None

                            if page_obj:
                                # 获取页码（从 0 开始，需要 +1）
                                page_num = reader.pages.index(page_obj) + 1

                                # 简单处理：假设章节从当前页到下一章节前一页
                                # 实际应用中可能需要更复杂的逻辑
                                chapters.append(Chapter(
                                    title=title,
                                    start_page=page_num,
                                    end_page=page_num,  # 临时设置，后续需要调整
                                    level=level
                                ))
                        except Exception:
                            continue

            extract_outline(outlines)

            # 调整章节结束页码
            for i in range(len(chapters) - 1):
                chapters[i].end_page = chapters[i + 1].start_page - 1

            # 最后一章到文档末尾
            if chapters:
                chapters[-1].end_page = len(reader.pages)

        except Exception:
            # 如果提取失败，返回空列表
            pass

        return chapters

    def _extract_metadata(self, reader: PdfReader) -> dict:
        """提取 PDF 元数据

        Args:
            reader: PdfReader 对象

        Returns:
            元数据字典
        """
        metadata = {}

        try:
            if reader.metadata:
                # 提取常见元数据字段
                if reader.metadata.title:
                    metadata['title'] = reader.metadata.title
                if reader.metadata.author:
                    metadata['author'] = reader.metadata.author
                if reader.metadata.subject:
                    metadata['subject'] = reader.metadata.subject
                if reader.metadata.creator:
                    metadata['creator'] = reader.metadata.creator
                if reader.metadata.producer:
                    metadata['producer'] = reader.metadata.producer
        except Exception:
            pass

        return metadata
