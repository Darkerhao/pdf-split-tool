"""Application State Service - Manages application-wide state"""
from typing import List, Optional
from domain.repositories.settings_repository import ISettingsRepository, AppSettings


class AppStateService:
    """
    Application state service that coordinates settings persistence
    and provides application-wide state management
    """

    def __init__(self, settings_repository: ISettingsRepository):
        self._settings_repo = settings_repository
        self._current_settings: Optional[AppSettings] = None

    def load_settings(self) -> AppSettings:
        """Load application settings from repository"""
        self._current_settings = self._settings_repo.load()
        return self._current_settings

    def save_settings(self, settings: AppSettings) -> None:
        """Save application settings to repository"""
        self._settings_repo.save(settings)
        self._current_settings = settings

    def get_current_settings(self) -> AppSettings:
        """Get current settings (loads if not already loaded)"""
        if self._current_settings is None:
            self._current_settings = self.load_settings()
        return self._current_settings

    def update_language(self, language: str) -> None:
        """Update application language"""
        settings = self.get_current_settings()
        settings.language = language
        self.save_settings(settings)

    def add_recent_file(self, file_path: str) -> None:
        """Add a file to recent files list"""
        settings = self.get_current_settings()
        self._settings_repo.add_recent_file(file_path)
        # Reload to get updated recent files
        self._current_settings = self._settings_repo.load()

    def get_recent_files(self) -> List[str]:
        """Get recent files list"""
        settings = self.get_current_settings()
        return settings.recent_files

    def clear_recent_files(self) -> None:
        """Clear all recent files"""
        self._settings_repo.clear_recent_files()
        self._current_settings = self._settings_repo.load()

    def update_template(self, template: str) -> None:
        """Update output filename template"""
        settings = self.get_current_settings()
        settings.output_template = template
        self.save_settings(settings)

    def get_template(self) -> str:
        """Get current output filename template"""
        settings = self.get_current_settings()
        return settings.output_template
