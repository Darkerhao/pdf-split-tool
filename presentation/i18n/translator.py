"""Translator - Internationalization support"""
import json
import os
from typing import Dict, Optional


class Translator:
    """
    Translator for internationalization support

    Loads translation strings from JSON files and provides lookup functionality.
    """

    def __init__(self, locales_dir: str = None):
        """
        Initialize translator

        Args:
            locales_dir: Directory containing locale JSON files
        """
        if locales_dir is None:
            # Default to locales directory next to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            locales_dir = os.path.join(current_dir, "locales")

        self.locales_dir = locales_dir
        self._translations: Dict[str, Dict[str, str]] = {}
        self._current_language = "zh_CN"  # Default to zh_CN instead of "zh"
        self._load_translations()

    def _load_translations(self) -> None:
        """Load all translation files from locales directory"""
        if not os.path.exists(self.locales_dir):
            return

        for filename in os.listdir(self.locales_dir):
            if filename.endswith('.json'):
                locale_code = filename.replace('.json', '')
                file_path = os.path.join(self.locales_dir, filename)

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self._translations[locale_code] = json.load(f)
                except Exception as e:
                    print(f"Failed to load translation file {filename}: {e}")

    def set_language(self, language: str) -> None:
        """
        Set current language

        Args:
            language: Language code (zh, en, zh_CN, en_US)
        """
        # Normalize language code
        if language == "zh":
            language = "zh_CN"
        elif language == "en":
            language = "en_US"

        if language in self._translations:
            self._current_language = language
        else:
            print(f"Warning: Language '{language}' not found, using default")

    def get_language(self) -> str:
        """Get current language code"""
        return self._current_language

    def translate(self, key: str, default: Optional[str] = None) -> str:
        """
        Translate a key to current language

        Args:
            key: Translation key
            default: Default value if key not found

        Returns:
            Translated string, or key itself if not found
        """
        translations = self._translations.get(self._current_language, {})
        return translations.get(key, default or key)

    def __call__(self, key: str) -> str:
        """Shorthand for translate()"""
        return self.translate(key)

    def get_available_languages(self) -> list:
        """Get list of available language codes"""
        return list(self._translations.keys())


# Global translator instance
_translator: Optional[Translator] = None


def get_translator() -> Translator:
    """Get global translator instance"""
    global _translator
    if _translator is None:
        _translator = Translator()
    return _translator


def T(key: str) -> str:
    """
    Convenience function for translation

    Args:
        key: Translation key

    Returns:
        Translated string
    """
    return get_translator().translate(key)
