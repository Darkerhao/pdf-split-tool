"""设置仓储接口"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List


@dataclass
class AppSettings:
    """应用设置领域模型"""
    input_file: str = ""
    output_file: str = ""
    dark_theme: bool = False
    language: str = "zh"
    recent_files: List[str] = field(default_factory=list)
    output_template: str = "{name}_{start}-{end}.pdf"
    epub_input: str = ""
    epub_output: str = ""
    epub_paper: str = "a4"


class ISettingsRepository(ABC):
    """设置仓储接口

    负责应用设置的持久化
    """

    @abstractmethod
    def load(self) -> AppSettings:
        """加载应用设置

        Returns:
            AppSettings 对象，如果文件不存在返回默认设置
        """
        pass

    @abstractmethod
    def save(self, settings: AppSettings) -> None:
        """保存应用设置

        Args:
            settings: 要保存的设置对象
        """
        pass

    @abstractmethod
    def add_recent_file(self, file_path: str) -> None:
        """添加最近文件

        Args:
            file_path: 文件路径
        """
        pass

    @abstractmethod
    def clear_recent_files(self) -> None:
        """清空最近文件列表"""
        pass
