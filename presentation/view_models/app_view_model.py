"""App View Model - Main application view model"""
from typing import List
from .base_view_model import BaseViewModel
from application.services.app_state_service import AppStateService


class AppViewModel(BaseViewModel):
    """
    Main application view model

    Manages:
    - Application settings
    - Recent files
    - Language switching
    - Theme switching

    Events:
    - language_changed: Fired when language changes (language: str)
    - theme_changed: Fired when theme changes (theme: str)
    - recent_files_updated: Fired when recent files list changes (files: List[str])
    """

    def __init__(self, app_state_service: AppStateService):
        super().__init__()
        self._app_state = app_state_service

        # Load initial settings
        settings = self._app_state.load_settings()

        # Properties
        self._language: str = settings.language
        self._theme: str = "light" if not settings.dark_theme else "dark"
        self._recent_files: List[str] = settings.recent_files
        self._template: str = settings.output_template

    @property
    def language(self) -> str:
        return self._language

    @language.setter
    def language(self, value: str):
        if self._language != value:
            self._language = value
            self._app_state.update_language(value)
            self._notify_property_changed("language", value)
            self._raise_event("language_changed", value)

    @property
    def theme(self) -> str:
        return self._theme

    @theme.setter
    def theme(self, value: str):
        if self._theme != value:
            self._theme = value
            self._notify_property_changed("theme", value)
            self._raise_event("theme_changed", value)

    @property
    def recent_files(self) -> List[str]:
        return self._recent_files

    @property
    def template(self) -> str:
        return self._template

    @template.setter
    def template(self, value: str):
        if self._template != value:
            self._template = value
            self._app_state.update_template(value)
            self._notify_property_changed("template", value)

    def add_recent_file(self, file_path: str) -> None:
        """Add a file to recent files list"""
        self._app_state.add_recent_file(file_path)
        self._recent_files = self._app_state.get_recent_files()
        self._notify_property_changed("recent_files", self._recent_files)
        self._raise_event("recent_files_updated", self._recent_files)

    def clear_recent_files(self) -> None:
        """Clear all recent files"""
        self._app_state.clear_recent_files()
        self._recent_files = []
        self._notify_property_changed("recent_files", self._recent_files)
        self._raise_event("recent_files_updated", self._recent_files)

    def get_recent_files(self) -> List[str]:
        """Get current recent files list"""
        return self._recent_files
