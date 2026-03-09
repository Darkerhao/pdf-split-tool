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
    import split_pdf_gui_app  # noqa: F401


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
