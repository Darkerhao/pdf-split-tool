"""页码范围值对象"""
from typing import List


class PageRange:
    """页码范围值对象（不可变）

    值对象代表没有概念标识的领域概念，通过属性值来识别。
    页码范围是不可变的，两个相同范围的对象应该被认为是相等的。
    """
    __slots__ = ('start', 'end')

    def __init__(self, start: int, end: int):
        """创建页码范围

        Args:
            start: 起始页码
            end: 结束页码

        Raises:
            ValueError: 页码无效
        """
        # 先交换，确保 start <= end
        if start > end:
            start, end = end, start

        # 验证页码必须大于 0
        if start <= 0 or end <= 0:
            raise ValueError(f"页码必须大于 0，当前：start={start}, end={end}")

        object.__setattr__(self, 'start', start)
        object.__setattr__(self, 'end', end)

    def __setattr__(self, name, value):
        """禁止修改属性（不可变）"""
        raise AttributeError(f"PageRange 是不可变对象，不能修改属性 {name}")

    def __eq__(self, other):
        """相等性比较"""
        if not isinstance(other, PageRange):
            return False
        return self.start == other.start and self.end == other.end

    def __hash__(self):
        """哈希值"""
        return hash((self.start, self.end))

    def __repr__(self):
        """调试表示"""
        return f"PageRange(start={self.start}, end={self.end})"

    @property
    def page_count(self) -> int:
        """获取页码范围包含的页数"""
        return self.end - self.start + 1

    def overlaps_with(self, other: 'PageRange') -> bool:
        """判断两个范围是否重叠"""
        return not (self.end < other.start or self.start > other.end)

    def contains_page(self, page: int) -> bool:
        """判断是否包含指定页码"""
        return self.start <= page <= self.end

    @classmethod
    def parse(cls, range_str: str) -> 'PageRange':
        """解析字符串为页码范围

        支持格式：
        - "10" -> PageRange(10, 10)
        - "1-10" -> PageRange(1, 10)
        - "10-1" -> PageRange(1, 10) (自动纠正)

        Args:
            range_str: 范围字符串

        Returns:
            PageRange 对象

        Raises:
            ValueError: 格式无效时
        """
        range_str = range_str.strip()
        if not range_str:
            raise ValueError("范围字符串不能为空")

        if '-' in range_str:
            parts = range_str.split('-', 1)
            if len(parts) != 2:
                raise ValueError(f"无效的范围格式: {range_str}")

            try:
                start = int(parts[0].strip())
                end = int(parts[1].strip())
                return cls(start, end)
            except ValueError as e:
                raise ValueError(f"无法解析页码: {range_str}") from e
        else:
            try:
                page = int(range_str)
                return cls(page, page)
            except ValueError as e:
                raise ValueError(f"无法解析页码: {range_str}") from e

    @classmethod
    def parse_multiple(cls, ranges_str: str) -> List['PageRange']:
        """解析多个范围字符串

        支持格式：
        - "1-3,5,7-9" -> [PageRange(1,3), PageRange(5,5), PageRange(7,9)]
        - "1-3，5，7-9" -> 同上（支持中文逗号）

        Args:
            ranges_str: 多范围字符串

        Returns:
            PageRange 列表
        """
        # 统一替换中文逗号
        normalized = ranges_str.replace('，', ',').strip()
        if not normalized:
            return []

        ranges: List[PageRange] = []
        for part in normalized.split(','):
            part = part.strip()
            if not part:
                continue

            try:
                page_range = cls.parse(part)
                ranges.append(page_range)
            except ValueError:
                # 跳过无效范围
                continue

        return ranges

    def __str__(self) -> str:
        """字符串表示"""
        if self.start == self.end:
            return str(self.start)
        return f"{self.start}-{self.end}"
