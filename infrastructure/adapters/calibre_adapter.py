"""Calibre EPUB 转换适配器"""
import os
import shutil
import subprocess
from typing import Callable

from domain.services.epub_service import IEPUBConverter
from domain.models.epub_document import EPUBDocument, PaperSize
from shared.exceptions.domain_exceptions import ConversionFailedError


def find_ebook_convert() -> str:
    """查找 Calibre 的 ebook-convert 可执行文件路径"""
    # 首先尝试从 PATH 查找
    path = shutil.which("ebook-convert")
    if path:
        return path

    # Windows 常见安装路径
    candidates = [
        os.path.join("C:\\Program Files\\Calibre", "ebook-convert.exe"),
        os.path.join("C:\\Program Files (x86)\\Calibre", "ebook-convert.exe"),
        os.path.join("C:\\Program Files\\Calibre2", "ebook-convert.exe"),
    ]

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    return ""


class CalibreAdapter(IEPUBConverter):
    """使用 Calibre ebook-convert 实现的 EPUB 转换器"""

    def __init__(self):
        self._ebook_convert_path = find_ebook_convert()

    def convert(
        self,
        document: EPUBDocument,
        output_path: str,
        paper_size: PaperSize = PaperSize.A4,
        progress_callback: Callable[[float, str], None] = None
    ) -> str:
        """将 EPUB 转换为 PDF

        Args:
            document: EPUB 文档对象
            output_path: 输出 PDF 文件路径
            paper_size: 纸张大小
            progress_callback: 进度回调函数

        Returns:
            输出文件路径

        Raises:
            ConversionFailedError: 转换失败
        """
        if not self.is_available():
            raise ConversionFailedError("Calibre ebook-convert 不可用")

        if progress_callback:
            progress_callback(0.0, "开始转换 EPUB 到 PDF")

        # 构建命令
        cmd = [
            self._ebook_convert_path,
            document.path,
            output_path,
            f"--paper-size={paper_size.value}",
            "--pdf-default-font-size=12",
            "--pdf-mono-font-size=12"
        ]

        try:
            # 执行转换
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # 监控进度
            for line in process.stdout:
                # Calibre 输出进度信息，尝试解析
                if progress_callback and '%' in line:
                    try:
                        # 简单解析进度百分比
                        import re
                        match = re.search(r'(\d+)%', line)
                        if match:
                            progress = float(match.group(1))
                            progress_callback(progress, f"转换中: {progress:.0f}%")
                    except Exception:
                        pass

            # 等待完成
            return_code = process.wait()

            if return_code != 0:
                stderr = process.stderr.read()
                raise ConversionFailedError(f"Calibre 转换失败: {stderr}")

            if progress_callback:
                progress_callback(100.0, "转换完成！")

            return output_path

        except Exception as e:
            if isinstance(e, ConversionFailedError):
                raise
            raise ConversionFailedError(f"EPUB 转换失败: {str(e)}") from e

    def is_available(self) -> bool:
        """检查转换器是否可用

        Returns:
            True 如果 Calibre 可用
        """
        return bool(self._ebook_convert_path)

    def get_name(self) -> str:
        """获取转换器名称

        Returns:
            "Calibre"
        """
        return "Calibre"
