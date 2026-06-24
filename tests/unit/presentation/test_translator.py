"""Unit tests for Translator"""
import unittest
import json
import os
import tempfile
import shutil
from presentation.i18n.translator import Translator


class TestTranslator(unittest.TestCase):
    """Test cases for Translator"""

    def setUp(self):
        """Set up test fixtures"""
        # Create temporary locales directory
        self.temp_dir = tempfile.mkdtemp()
        self.locales_dir = os.path.join(self.temp_dir, "locales")
        os.makedirs(self.locales_dir)

        # Create test translation files
        zh_translations = {
            "hello": "你好",
            "world": "世界",
            "greeting": "你好，{name}"
        }

        en_translations = {
            "hello": "Hello",
            "world": "World",
            "greeting": "Hello, {name}"
        }

        with open(os.path.join(self.locales_dir, "zh_CN.json"), 'w', encoding='utf-8') as f:
            json.dump(zh_translations, f, ensure_ascii=False)

        with open(os.path.join(self.locales_dir, "en_US.json"), 'w', encoding='utf-8') as f:
            json.dump(en_translations, f, ensure_ascii=False)

        self.translator = Translator(self.locales_dir)

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)

    def test_translate_default_language(self):
        """Test translation with default language (zh)"""
        # Assert
        self.assertEqual(self.translator.translate("hello"), "你好")
        self.assertEqual(self.translator.translate("world"), "世界")

    def test_translate_after_language_change(self):
        """Test translation after changing language"""
        # Act
        self.translator.set_language("en")

        # Assert
        self.assertEqual(self.translator.translate("hello"), "Hello")
        self.assertEqual(self.translator.translate("world"), "World")

    def test_translate_missing_key(self):
        """Test translation with missing key returns key itself"""
        # Assert
        self.assertEqual(self.translator.translate("missing_key"), "missing_key")

    def test_translate_with_default(self):
        """Test translation with default value"""
        # Assert
        self.assertEqual(self.translator.translate("missing_key", "Default"), "Default")

    def test_callable_shorthand(self):
        """Test using translator as callable"""
        # Assert
        self.assertEqual(self.translator("hello"), "你好")

    def test_get_available_languages(self):
        """Test getting available languages"""
        # Act
        languages = self.translator.get_available_languages()

        # Assert
        self.assertIn("zh_CN", languages)
        self.assertIn("en_US", languages)

    def test_normalize_language_code(self):
        """Test language code normalization"""
        # Act
        self.translator.set_language("zh")

        # Assert
        self.assertEqual(self.translator.get_language(), "zh_CN")

        # Act
        self.translator.set_language("en")

        # Assert
        self.assertEqual(self.translator.get_language(), "en_US")


if __name__ == '__main__':
    unittest.main()
