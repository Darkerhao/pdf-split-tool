"""JSON 设置仓储实现"""
import json
import os
from typing import List

from domain.repositories.settings_repository import ISettingsRepository, AppSettings


class JSONSettingsRepository(ISettingsRepository):
    """使用 JSON 文件实现的设置仓储"""

    def __init__(self, settings_path: str):
        """初始化仓储

        Args:
            settings_path: JSON 设置文件路径
        """
        self._settings_path = settings_path

    def load(self) -> AppSettings:
        """加载应用设置

        Returns:
            AppSettings 对象，如果文件不存在返回默认设置
        """
        if not os.path.exists(self._settings_path):
            return AppSettings()

        try:
            with open(self._settings_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not isinstance(data, dict):
                return AppSettings()

            # 从 JSON 数据构建 AppSettings
            return AppSettings(
                input_file=self._normalize_string(data.get('input', '')),
                output_file=self._normalize_string(data.get('output', '')),
                dark_theme=bool(data.get('dark', False)),
                language=self._normalize_language(data.get('lang', 'zh')),
                recent_files=self._normalize_recent_files(data.get('recent', [])),
                output_template=self._normalize_string(
                    data.get('template', '{name}_{start}-{end}.pdf')
                ),
                epub_input=self._normalize_string(data.get('epub_input', '')),
                epub_output=self._normalize_string(data.get('epub_output', '')),
                epub_paper=self._normalize_string(data.get('epub_paper', 'a4'))
            )
        except Exception:
            return AppSettings()

    def save(self, settings: AppSettings) -> None:
        """保存应用设置

        Args:
            settings: 要保存的设置对象
        """
        data = {
            'input': settings.input_file,
            'output': settings.output_file,
            'dark': settings.dark_theme,
            'lang': settings.language,
            'recent': settings.recent_files,
            'template': settings.output_template,
            'epub_input': settings.epub_input,
            'epub_output': settings.epub_output,
            'epub_paper': settings.epub_paper
        }

        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self._settings_path), exist_ok=True)

            with open(self._settings_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            # 保存失败时静默处理（可选：记录日志）
            pass

    def add_recent_file(self, file_path: str) -> None:
        """添加最近文件

        Args:
            file_path: 文件路径
        """
        settings = self.load()

        # 规范化路径
        normalized_path = os.path.normpath(os.path.abspath(file_path))

        # 移除重复项（不区分大小写）
        recent_files = [
            f for f in settings.recent_files
            if os.path.normcase(f) != os.path.normcase(normalized_path)
        ]

        # 添加到列表开头
        recent_files.insert(0, normalized_path)

        # 限制数量（最多 8 个）
        recent_files = recent_files[:8]

        # 更新并保存
        settings.recent_files = recent_files
        self.save(settings)

    def clear_recent_files(self) -> None:
        """清空最近文件列表"""
        settings = self.load()
        settings.recent_files = []
        self.save(settings)

    @staticmethod
    def _normalize_string(value, default: str = '') -> str:
        """规范化字符串"""
        if not isinstance(value, str):
            return default
        normalized = value.strip()
        return normalized if normalized else default

    @staticmethod
    def _normalize_language(lang: str) -> str:
        """规范化语言代码"""
        supported = {'zh', 'en'}
        normalized = lang.strip().lower()
        return normalized if normalized in supported else 'zh'

    @staticmethod
    def _normalize_recent_files(files) -> List[str]:
        """规范化最近文件列表"""
        if not isinstance(files, (list, tuple)):
            return []

        normalized = []
        seen = set()

        for item in files:
            if not isinstance(item, str):
                continue

            path = item.strip()
            if not path:
                continue

            # 规范化路径
            try:
                path = os.path.normpath(os.path.abspath(path))
            except Exception:
                continue

            # 去重（不区分大小写）
            key = os.path.normcase(path)
            if key in seen:
                continue

            seen.add(key)
            normalized.append(path)

            # 限制数量
            if len(normalized) >= 8:
                break

        return normalized
