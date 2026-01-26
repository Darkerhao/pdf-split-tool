from dataclasses import dataclass
from typing import Callable, Optional, Any


@dataclass
class TaskContext:
    """
    任务执行上下文（与 UI / 框架无关）
    """

    # 是否被请求取消
    is_cancelled: Callable[[], bool]

    # 上报进度：0~100
    report_progress: Callable[[float, str], None]

    # 正常完成
    report_done: Callable[[str, Optional[Any]], None]

    # 发生错误
    report_error: Callable[[str], None]

    def check_cancelled(self):
        """
        统一的取消检测点
        """
        if self.is_cancelled():
            raise TaskCancelledError()


class TaskCancelledError(Exception):
    """任务被用户取消"""
    pass