"""JSON 设置仓储测试"""
import unittest
import os
import tempfile
import json

from infrastructure.repositories.json_settings_repository import JSONSettingsRepository
from domain.repositories.settings_repository import AppSettings


class TestJSONSettingsRepository(unittest.TestCase):
    """JSON 设置仓储测试"""

    def setUp(self):
        """测试前准备"""
        # 创建临时文件
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.settings_path = self.temp_file.name
        self.repo = JSONSettingsRepository(self.settings_path)

    def tearDown(self):
        """测试后清理"""
        try:
            os.unlink(self.settings_path)
        except Exception:
            pass

    def test_load_default_when_file_not_exists(self):
        """测试文件不存在时加载默认设置"""
        # 删除临时文件
        os.unlink(self.settings_path)

        settings = self.repo.load()

        self.assertIsInstance(settings, AppSettings)
        self.assertEqual(settings.language, 'zh')
        self.assertEqual(settings.dark_theme, False)
        self.assertEqual(settings.recent_files, [])

    def test_save_and_load(self):
        """测试保存和加载"""
        # 创建设置
        settings = AppSettings(
            input_file='test.pdf',
            output_file='output.pdf',
            dark_theme=True,
            language='en',
            recent_files=['/path/to/file1.pdf', '/path/to/file2.pdf']
        )

        # 保存
        self.repo.save(settings)

        # 加载
        loaded = self.repo.load()

        self.assertEqual(loaded.input_file, 'test.pdf')
        self.assertEqual(loaded.output_file, 'output.pdf')
        self.assertEqual(loaded.dark_theme, True)
        self.assertEqual(loaded.language, 'en')
        self.assertEqual(len(loaded.recent_files), 2)

    def test_add_recent_file(self):
        """测试添加最近文件"""
        # 添加文件
        self.repo.add_recent_file('/path/to/file1.pdf')
        self.repo.add_recent_file('/path/to/file2.pdf')

        # 加载并验证
        settings = self.repo.load()
        self.assertEqual(len(settings.recent_files), 2)
        # 最新的在前
        self.assertIn('file2.pdf', settings.recent_files[0])
        self.assertIn('file1.pdf', settings.recent_files[1])

    def test_add_recent_file_deduplication(self):
        """测试最近文件去重"""
        # 添加相同文件
        self.repo.add_recent_file('/path/to/file.pdf')
        self.repo.add_recent_file('/path/to/file.pdf')

        settings = self.repo.load()
        self.assertEqual(len(settings.recent_files), 1)

    def test_add_recent_file_limit(self):
        """测试最近文件数量限制（最多 8 个）"""
        # 添加 10 个文件
        for i in range(10):
            self.repo.add_recent_file(f'/path/to/file{i}.pdf')

        settings = self.repo.load()
        # 应该只保留最新的 8 个
        self.assertEqual(len(settings.recent_files), 8)
        self.assertIn('file9.pdf', settings.recent_files[0])

    def test_clear_recent_files(self):
        """测试清空最近文件"""
        # 添加文件
        self.repo.add_recent_file('/path/to/file.pdf')

        # 清空
        self.repo.clear_recent_files()

        settings = self.repo.load()
        self.assertEqual(len(settings.recent_files), 0)

    def test_normalize_language(self):
        """测试语言规范化"""
        settings = AppSettings(language='invalid')
        self.repo.save(settings)

        loaded = self.repo.load()
        # 无效语言应该回退到默认值 'zh'
        self.assertEqual(loaded.language, 'zh')


if __name__ == '__main__':
    unittest.main()
