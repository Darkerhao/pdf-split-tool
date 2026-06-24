"""Unit tests for App State Service"""
import unittest
from unittest.mock import Mock
from domain.repositories.settings_repository import ISettingsRepository, AppSettings
from application.services.app_state_service import AppStateService


class TestAppStateService(unittest.TestCase):
    """Test cases for AppStateService"""

    def setUp(self):
        """Set up test fixtures"""
        self.settings_repo = Mock(spec=ISettingsRepository)
        self.service = AppStateService(self.settings_repo)

    def test_load_settings(self):
        """Test loading settings"""
        # Arrange
        expected_settings = AppSettings(language="en", output_template="test_{index}.pdf")
        self.settings_repo.load.return_value = expected_settings

        # Act
        result = self.service.load_settings()

        # Assert
        self.assertEqual(result, expected_settings)
        self.settings_repo.load.assert_called_once()

    def test_save_settings(self):
        """Test saving settings"""
        # Arrange
        settings = AppSettings(language="zh", output_template="custom_{name}.pdf")

        # Act
        self.service.save_settings(settings)

        # Assert
        self.settings_repo.save.assert_called_once_with(settings)

    def test_get_current_settings_loads_if_not_cached(self):
        """Test that get_current_settings loads settings if not already loaded"""
        # Arrange
        expected_settings = AppSettings(language="en")
        self.settings_repo.load.return_value = expected_settings

        # Act
        result = self.service.get_current_settings()

        # Assert
        self.assertEqual(result, expected_settings)
        self.settings_repo.load.assert_called_once()

    def test_get_current_settings_returns_cached(self):
        """Test that get_current_settings returns cached settings"""
        # Arrange
        settings = AppSettings(language="en")
        self.service._current_settings = settings

        # Act
        result = self.service.get_current_settings()

        # Assert
        self.assertEqual(result, settings)
        self.settings_repo.load.assert_not_called()

    def test_update_language(self):
        """Test updating language"""
        # Arrange
        initial_settings = AppSettings(language="en")
        self.settings_repo.load.return_value = initial_settings

        # Act
        self.service.update_language("zh")

        # Assert
        self.assertEqual(self.service._current_settings.language, "zh")
        self.settings_repo.save.assert_called_once()

    def test_add_recent_file(self):
        """Test adding a recent file"""
        # Arrange
        initial_settings = AppSettings(recent_files=[])
        updated_settings = AppSettings(recent_files=["file.pdf"])
        self.settings_repo.load.side_effect = [initial_settings, updated_settings]

        # Act
        self.service.add_recent_file("file.pdf")

        # Assert
        self.settings_repo.add_recent_file.assert_called_once_with("file.pdf")
        # Should reload settings after adding
        self.assertEqual(self.settings_repo.load.call_count, 2)

    def test_get_recent_files(self):
        """Test getting recent files"""
        # Arrange
        settings = AppSettings(recent_files=["file1.pdf", "file2.pdf"])
        self.settings_repo.load.return_value = settings

        # Act
        result = self.service.get_recent_files()

        # Assert
        self.assertEqual(result, ["file1.pdf", "file2.pdf"])

    def test_clear_recent_files(self):
        """Test clearing recent files"""
        # Arrange
        initial_settings = AppSettings(recent_files=["file.pdf"])
        updated_settings = AppSettings(recent_files=[])
        # First call loads initial settings, second call reloads after clear
        self.settings_repo.load.side_effect = [initial_settings, updated_settings]

        # Load initial settings first
        self.service.load_settings()

        # Act
        self.service.clear_recent_files()

        # Assert
        self.settings_repo.clear_recent_files.assert_called_once()
        # Should reload settings after clearing
        self.assertEqual(self.settings_repo.load.call_count, 2)

    def test_update_template(self):
        """Test updating template"""
        # Arrange
        initial_settings = AppSettings(output_template="{name}.pdf")
        self.settings_repo.load.return_value = initial_settings

        # Act
        self.service.update_template("{name}_{index}.pdf")

        # Assert
        self.assertEqual(self.service._current_settings.output_template, "{name}_{index}.pdf")
        self.settings_repo.save.assert_called_once()

    def test_get_template(self):
        """Test getting template"""
        # Arrange
        settings = AppSettings(output_template="{name}_{start}-{end}.pdf")
        self.settings_repo.load.return_value = settings

        # Act
        result = self.service.get_template()

        # Assert
        self.assertEqual(result, "{name}_{start}-{end}.pdf")


if __name__ == '__main__':
    unittest.main()
