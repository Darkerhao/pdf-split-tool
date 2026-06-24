"""领域层单元测试"""
import unittest
from domain.models.page_range import PageRange


class TestPageRange(unittest.TestCase):
    """页码范围值对象测试"""

    def test_create_valid_range(self):
        """测试创建有效范围"""
        r = PageRange(1, 10)
        self.assertEqual(r.start, 1)
        self.assertEqual(r.end, 10)
        self.assertEqual(r.page_count, 10)

    def test_create_single_page(self):
        """测试创建单页范围"""
        r = PageRange(5, 5)
        self.assertEqual(r.start, 5)
        self.assertEqual(r.end, 5)
        self.assertEqual(r.page_count, 1)

    def test_auto_swap_start_end(self):
        """测试自动交换起止页码"""
        r = PageRange(10, 1)
        self.assertEqual(r.start, 1)
        self.assertEqual(r.end, 10)

    def test_invalid_page_numbers(self):
        """测试无效页码"""
        with self.assertRaises(ValueError):
            PageRange(0, 10)
        with self.assertRaises(ValueError):
            PageRange(-1, 10)

    def test_parse_single_page(self):
        """测试解析单页"""
        r = PageRange.parse("5")
        self.assertEqual(r.start, 5)
        self.assertEqual(r.end, 5)

    def test_parse_range(self):
        """测试解析范围"""
        r = PageRange.parse("1-10")
        self.assertEqual(r.start, 1)
        self.assertEqual(r.end, 10)

    def test_parse_reversed_range(self):
        """测试解析反向范围"""
        r = PageRange.parse("10-1")
        self.assertEqual(r.start, 1)
        self.assertEqual(r.end, 10)

    def test_parse_multiple(self):
        """测试解析多个范围"""
        ranges = PageRange.parse_multiple("1-3,5,7-9")
        self.assertEqual(len(ranges), 3)
        self.assertEqual(ranges[0], PageRange(1, 3))
        self.assertEqual(ranges[1], PageRange(5, 5))
        self.assertEqual(ranges[2], PageRange(7, 9))

    def test_parse_multiple_with_chinese_comma(self):
        """测试解析多个范围（中文逗号）"""
        ranges = PageRange.parse_multiple("1-3，5，7-9")
        self.assertEqual(len(ranges), 3)

    def test_overlaps_with(self):
        """测试范围重叠"""
        r1 = PageRange(1, 5)
        r2 = PageRange(3, 8)
        r3 = PageRange(10, 15)

        self.assertTrue(r1.overlaps_with(r2))
        self.assertFalse(r1.overlaps_with(r3))

    def test_contains_page(self):
        """测试包含页码"""
        r = PageRange(5, 10)
        self.assertTrue(r.contains_page(5))
        self.assertTrue(r.contains_page(7))
        self.assertTrue(r.contains_page(10))
        self.assertFalse(r.contains_page(4))
        self.assertFalse(r.contains_page(11))

    def test_str_representation(self):
        """测试字符串表示"""
        self.assertEqual(str(PageRange(1, 10)), "1-10")
        self.assertEqual(str(PageRange(5, 5)), "5")


if __name__ == '__main__':
    unittest.main()
