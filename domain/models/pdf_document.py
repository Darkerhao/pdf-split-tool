"""PDF 文档领域模型"""
from dataclasses import dataclass, field
from typing import List, Optional
from .page_range import PageRange


@dataclass
class Chapter:
    """章节模型"""
    title: str
    start_page: int
    end_page: int
    level: int = 0  # 章节层级（0=一级标题，1=二级标题）

    @property
    def page_range(self) -> PageRange:
        """获取章节的页码范围"""
        return PageRange(self.start_page, self.end_page)

    @property
    def page_count(self) -> int:
        """获取章节页数"""
        return self.end_page - self.start_page + 1


@dataclass
class PDFDocument:
    """PDF 文档领域模型

    聚合根：代表一个完整的 PDF 文档，包含页码信息和章节结构
    """
    path: str
    total_pages: int
    chapters: List[Chapter] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        """验证文档的有效性"""
        if self.total_pages <= 0:
            raise ValueError(f"PDF 总页数必须大于 0，当前：{self.total_pages}")

    def validate_range(self, page_range: PageRange) -> bool:
        """验证页码范围是否在文档有效范围内

        Args:
            page_range: 要验证的页码范围

        Returns:
            True 如果范围有效
        """
        return 1 <= page_range.start <= self.total_pages and \
               1 <= page_range.end <= self.total_pages

    def normalize_range(self, page_range: PageRange) -> PageRange:
        """规范化页码范围，将超出范围的页码裁剪到有效范围

        Args:
            page_range: 原始页码范围

        Returns:
            规范化后的页码范围
        """
        start = max(1, min(page_range.start, self.total_pages))
        end = min(self.total_pages, max(page_range.end, 1))

        if start > end:
            return PageRange(end, start)

        return PageRange(start, end)

    def normalize_ranges(self, ranges: List[PageRange]) -> List[PageRange]:
        """批量规范化页码范围，过滤掉完全无效的范围

        Args:
            ranges: 页码范围列表

        Returns:
            规范化后的有效范围列表
        """
        normalized: List[PageRange] = []

        for page_range in ranges:
            # 跳过完全超出范围的
            if page_range.start > self.total_pages or page_range.end < 1:
                continue

            normalized_range = self.normalize_range(page_range)
            normalized.append(normalized_range)

        return normalized

    def get_chapter_at_page(self, page: int) -> Optional[Chapter]:
        """获取指定页码所属的章节

        Args:
            page: 页码（从 1 开始）

        Returns:
            章节对象，如果没有找到则返回 None
        """
        for chapter in self.chapters:
            if chapter.start_page <= page <= chapter.end_page:
                return chapter
        return None

    def has_chapters(self) -> bool:
        """判断文档是否包含章节信息"""
        return len(self.chapters) > 0

    def get_chapters_by_level(self, level: int) -> List[Chapter]:
        """获取指定层级的章节

        Args:
            level: 章节层级（0=一级标题，1=二级标题）

        Returns:
            指定层级的章节列表
        """
        return [ch for ch in self.chapters if ch.level == level]
