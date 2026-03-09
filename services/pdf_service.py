from dataclasses import dataclass
from typing import List, Tuple

from PyPDF2 import PdfReader


PageRange = Tuple[int, int]


@dataclass(frozen=True)
class SplitPreviewResult:
    valid_count: int
    lines: List[str]


def parse_ranges(ranges_str: str) -> List[PageRange]:
    """解析输入的页码范围字符串，例如 ``1-3,5,7-9``。"""
    ranges: List[PageRange] = []
    normalized = (ranges_str or "").replace("，", ",").strip()
    if not normalized:
        return ranges

    for part in normalized.split(","):
        part = part.strip()
        if not part:
            continue

        if "-" in part:
            try:
                start_str, end_str = part.split("-", 1)
                start, end = int(start_str), int(end_str)
                if start > end:
                    start, end = end, start
                ranges.append((start, end))
            except ValueError:
                continue
        elif part.isdigit():
            page = int(part)
            ranges.append((page, page))

    return ranges


def normalize_page_ranges(ranges: List[PageRange], total_pages: int) -> List[PageRange]:
    normalized_ranges: List[PageRange] = []

    for start, end in ranges:
        if start > end:
            start, end = end, start

        start = max(1, start)
        end = min(total_pages, end)

        if start <= end:
            normalized_ranges.append((start, end))

    return normalized_ranges


def build_split_preview(input_file: str, page_ranges_str: str) -> SplitPreviewResult:
    ranges = parse_ranges(page_ranges_str)
    if not ranges:
        raise ValueError("请输入有效的页码范围！")

    reader = PdfReader(input_file)
    total_pages = len(reader.pages)

    lines: List[str] = []
    valid_count = 0
    for idx, (start, end) in enumerate(ranges, start=1):
        clamped_start = max(1, min(start, end))
        clamped_end = min(total_pages, max(start, end))

        if clamped_start > clamped_end:
            lines.append(f"{idx}) {start}-{end} 超出范围，跳过")
            continue

        page_count = clamped_end - clamped_start + 1
        lines.append(f"{idx}) {clamped_start}-{clamped_end} （{page_count} 页）")
        valid_count += 1

    return SplitPreviewResult(valid_count=valid_count, lines=lines)


def parse_chapter_ranges(chapters_input: str) -> List[PageRange]:
    chapter_ranges: List[PageRange] = []

    for index, line in enumerate((chapters_input or "").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue

        if "-" not in line:
            raise ValueError(f"第{index}行章节范围格式错误，缺少'-'：{line}")

        try:
            start_str, end_str = line.split("-", 1)
            start = int(start_str.strip())
            end = int(end_str.strip())
        except ValueError as exc:
            raise ValueError(f"第{index}行章节范围格式错误：{line}") from exc

        if start > end:
            start, end = end, start

        chapter_ranges.append((start, end))

    return chapter_ranges


def sanitize_filename(name: str) -> str:
    bad = '\\/:*?"<>|'
    for ch in bad:
        name = name.replace(ch, '_')
    return name


def render_template(base_name: str, start: int, end: int, index: int, template_text: str) -> str:
    if not template_text:
        template_text = "{name}_{start}-{end}.pdf"
    try:
        filename = template_text.format(name=base_name, start=start, end=end, index=index)
    except Exception:
        filename = f"{base_name}_{start}-{end}.pdf"
    return sanitize_filename(filename)
