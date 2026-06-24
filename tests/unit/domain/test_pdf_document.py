"""领域层单元测试 - PDF 文档模型"""
import unittest
from domain.models.pdf_document import PDFDocument, Chapter
from domain.models.page_range import PageRange


class TestPDFDocument(unittest.TestCase):
    """PDF 文档领域模型测试"""

    def test_create_valid_document(self):
        """测试创建有效文档"""
        doc = PDFDocument(path="test.pdf", total_pages=100)
        self.assertEqual(doc.path, "test.pdf")
        self.assertEqual(doc.total_pages, 100)
        self.assertEqual(len(doc.chapters), 0)

    def test_invalid_total_pages(self):
        """测试无效总页数"""
        with self.assertRaises(ValueError):
            PDFDocument(path="test.pdf", total_pages=0)
        with self.assertRaises(ValueError):
            PDFDocument(path="test.pdf", total_pages=-1)

    def test_validate_range(self):
        """测试验证范围"""
        doc = PDFDocument(path="test.pdf", total_pages=100)

        self.assertTrue(doc.validate_range(PageRange(1, 50)))
        self.assertTrue(doc.validate_range(PageRange(1, 100)))
        # 注意：PageRange(0, 50) 在构造时就会抛出异常，所以无法测试
        # 这里测试超出上界的情况
        self.assertFalse(doc.validate_range(PageRange(1, 101)))

    def test_normalize_range(self):
        """测试规范化范围"""
        doc = PDFDocument(path="test.pdf", total_pages=100)

        # 正常范围
        r1 = doc.normalize_range(PageRange(10, 20))
        self.assertEqual(r1, PageRange(10, 20))

        # 超出上界
        r2 = doc.normalize_range(PageRange(90, 110))
        self.assertEqual(r2, PageRange(90, 100))

        # 注意：起始小于 1 的情况在 PageRange 构造时就会抛出异常
        # normalize_range 主要用于裁剪超出文档范围的页码

    def test_normalize_ranges(self):
        """测试批量规范化范围"""
        doc = PDFDocument(path="test.pdf", total_pages=100)

        ranges = [
            PageRange(1, 10),
            PageRange(90, 110),  # 超出范围
            PageRange(200, 300),  # 完全超出，应被过滤
        ]

        normalized = doc.normalize_ranges(ranges)
        self.assertEqual(len(normalized), 2)
        self.assertEqual(normalized[0], PageRange(1, 10))
        self.assertEqual(normalized[1], PageRange(90, 100))

    def test_has_chapters(self):
        """测试是否包含章节"""
        doc1 = PDFDocument(path="test.pdf", total_pages=100)
        self.assertFalse(doc1.has_chapters())

        doc2 = PDFDocument(
            path="test.pdf",
            total_pages=100,
            chapters=[Chapter(title="第一章", start_page=1, end_page=50)]
        )
        self.assertTrue(doc2.has_chapters())

    def test_get_chapter_at_page(self):
        """测试获取页码所属章节"""
        chapters = [
            Chapter(title="第一章", start_page=1, end_page=50),
            Chapter(title="第二章", start_page=51, end_page=100),
        ]
        doc = PDFDocument(path="test.pdf", total_pages=100, chapters=chapters)

        ch1 = doc.get_chapter_at_page(25)
        self.assertIsNotNone(ch1)
        self.assertEqual(ch1.title, "第一章")

        ch2 = doc.get_chapter_at_page(75)
        self.assertIsNotNone(ch2)
        self.assertEqual(ch2.title, "第二章")

        ch_none = doc.get_chapter_at_page(0)
        self.assertIsNone(ch_none)


class TestChapter(unittest.TestCase):
    """章节模型测试"""

    def test_create_chapter(self):
        """测试创建章节"""
        ch = Chapter(title="第一章", start_page=1, end_page=50, level=0)
        self.assertEqual(ch.title, "第一章")
        self.assertEqual(ch.start_page, 1)
        self.assertEqual(ch.end_page, 50)
        self.assertEqual(ch.level, 0)

    def test_page_range_property(self):
        """测试页码范围属性"""
        ch = Chapter(title="第一章", start_page=1, end_page=50)
        r = ch.page_range
        self.assertEqual(r.start, 1)
        self.assertEqual(r.end, 50)

    def test_page_count_property(self):
        """测试页数属性"""
        ch = Chapter(title="第一章", start_page=1, end_page=50)
        self.assertEqual(ch.page_count, 50)


if __name__ == '__main__':
    unittest.main()
