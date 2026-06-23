"""基础测试：确保核心服务函数可导入且基本逻辑正确。"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.pdf_service import normalize_page_ranges, sanitize_filename, render_template


def test_normalize_page_ranges():
    # 单页
    assert normalize_page_ranges("5", 10) == [(5, 5)]
    # 范围
    assert normalize_page_ranges("1-3", 10) == [(1, 3)]
    # 多段
    assert normalize_page_ranges("1-3,5,7-9", 10) == [(1, 3), (5, 5), (7, 9)]
    # 带空格
    assert normalize_page_ranges(" 1 - 3 , 5 ", 10) == [(1, 3), (5, 5)]
    # 超出总页数应截断
    assert normalize_page_ranges("1-15", 10) == [(1, 10)]


def test_sanitize_filename():
    assert sanitize_filename("hello/world") == "hello_world"
    assert sanitize_filename("file:name") == "file_name"
    assert sanitize_filename("  spaces  ") == "spaces"


def test_render_template():
    result = render_template("{name}_{start}-{end}.pdf", "doc", 2, 5)
    assert result == "doc_2-5.pdf"


if __name__ == "__main__":
    test_normalize_page_ranges()
    test_sanitize_filename()
    test_render_template()
    print("All tests passed!")
