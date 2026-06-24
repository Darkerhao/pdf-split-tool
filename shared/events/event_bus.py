"""事件总线

提供解耦的事件发布-订阅机制，替代传统的回调函数。
"""
from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Event:
    """事件基类"""
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            object.__setattr__(self, 'timestamp', datetime.now())


@dataclass
class ProgressEvent(Event):
    """进度更新事件"""
    progress: float  # 0-100
    message: str


@dataclass
class TaskCompletedEvent(Event):
    """任务完成事件"""
    result: Any
    message: str = ""


@dataclass
class TaskErrorEvent(Event):
    """任务错误事件"""
    error: Exception
    message: str = ""


class EventBus:
    """事件总线（单例模式）

    使用示例：
        bus = EventBus.get_instance()
        bus.subscribe("progress", lambda e: print(f"Progress: {e.progress}%"))
        bus.publish("progress", ProgressEvent(progress=50, message="处理中..."))
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._subscribers: Dict[str, List[Callable]] = {}
        return cls._instance

    @classmethod
    def get_instance(cls) -> 'EventBus':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def subscribe(self, event_name: str, callback: Callable[[Event], None]) -> None:
        """订阅事件

        Args:
            event_name: 事件名称
            callback: 回调函数，接收 Event 对象
        """
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(callback)

    def unsubscribe(self, event_name: str, callback: Callable[[Event], None]) -> None:
        """取消订阅

        Args:
            event_name: 事件名称
            callback: 要移除的回调函数
        """
        if event_name in self._subscribers:
            try:
                self._subscribers[event_name].remove(callback)
            except ValueError:
                pass

    def publish(self, event_name: str, event: Event) -> None:
        """发布事件

        Args:
            event_name: 事件名称
            event: 事件对象
        """
        for callback in self._subscribers.get(event_name, []):
            try:
                callback(event)
            except Exception as e:
                # 避免回调异常影响其他订阅者
                print(f"事件处理错误 [{event_name}]: {e}")

    def clear_subscribers(self, event_name: str = None) -> None:
        """清空订阅者

        Args:
            event_name: 事件名称，如果为 None 则清空所有
        """
        if event_name:
            self._subscribers.pop(event_name, None)
        else:
            self._subscribers.clear()
