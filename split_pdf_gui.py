"""GUI 启动入口与可导入兼容层。

作为脚本执行时启动 `split_pdf_gui_app`。
作为模块导入时仅暴露核心服务函数，避免导入阶段直接创建 Tk 窗口。
"""

__version__ = "0.0.0"  # CI 构建时由版本注入脚本替换

from importlib import import_module

from services.epub_service import (
    EPUB_LIBS_AVAILABLE,
    batch_epub_to_pdf,
    do_epub_convert_with_progress,
    epub_to_pdf_python,
)
from services.pdf_service import (
    build_split_preview,
    normalize_page_ranges,
    parse_chapter_ranges,
    parse_ranges,
    render_template,
    sanitize_filename,
)


def main():
    return import_module("split_pdf_gui_app")


__all__ = [
    "EPUB_LIBS_AVAILABLE",
    "batch_epub_to_pdf",
    "build_split_preview",
    "do_epub_convert_with_progress",
    "epub_to_pdf_python",
    "main",
    "normalize_page_ranges",
    "parse_chapter_ranges",
    "parse_ranges",
    "render_template",
    "sanitize_filename",
]


if __name__ == "__main__":
    main()
