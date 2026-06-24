"""Unit tests for AppViewModel"""
import unittest
from unittest.mock import Mock
from presentation.view_models.app_view_model import AppViewModel
from domain.repositories.settings_repository import AppSettings


class TestAppViewModel(unittest.TestCase):
    """Test cases for AppViewModel"""

    def setUp(self):
        """Set up test fixtures"""
        self.app_state_service = Mock()

        # Mock load_settings to return default settings
        self.app_state_service.load_settings.return_value = AppSettings(
            language="zh",
            dark_theme=False,
            recent_files=["file1.pdf", "file2.pdf"],
            output_template="{name}_{start}-{end}.pdf"
        )

        self.view_model = AppViewModel(self.app_state_service)

    def test_initial_properties_loaded(self):
        """Test that initial properties are loaded from settings"""
        # Assert
        self.assertEqual(self.view_model.language, "zh")
        self.assertEqual(self.view_model.theme, "light")
        self.assertEqual(len(self.view_model.recent_files), 2)
        self.assertEqual(self.view_model.template, "{name}_{start}-{end}.pdf")

    def test_language_change_triggers_event(self):
        """Test that changing language triggers event"""
        # Arrange
        callback = Mock()
        self.view_model.subscribe_event("language_changed", callback)

        # Act
        self.view_model.language = "en"

        # Assert
        self.app_state_service.update_language.assert_called_once_with("en")
        callback.assert_called_once_with("en")

    def test_theme_change_triggers_event(self):
        """Test that changing theme triggers event"""
        # Arrange
        callback = Mock()
        self.view_model.subscribe_event("theme_changed", callback)

        # Act
        self.view_model.theme = "dark"

        # Assert
        callback.assert_called_once_with("dark")

    def test_add_recent_file(self):
        """Test adding a recent file"""
        # Arrange
        self.app_state_service.get_recent_files.return_value = ["file1.pdf", "file2.pdf", "file3.pdf"]

        callback = Mock()
        self.view_model.subscribe_event("recent_files_updated", callback)

        # Act
        self.view_model.add_recent_file("file3.pdf")

        # Assert
        self.app_state_service.add_recent_file.assert_called_once_with("file3.pdf")
        callback.assert_called_once()
        self.assertEqual(len(self.view_model.recent_files), 3)

    def test_clear_recent_files(self):
        """Test clearing recent files"""
        # Arrange
        callback = Mock()
        self.view_model.subscribe_event("recent_files_updated", callback)

        # Act
        self.view_model.clear_recent_files()

        # Assert
        self.app_state_service.clear_recent_files.assert_called_once()
        callback.assert_called_once()
        self.assertEqual(len(self.view_model.recent_files), 0)

    def test_template_update(self):
        """Test updating template"""
        # Act
        self.view_model.template = "{name}_{index}.pdf"

        # Assert
        self.app_state_service.update_template.assert_called_once_with("{name}_{index}.pdf")


if __name__ == '__main__':
    unittest.main()
