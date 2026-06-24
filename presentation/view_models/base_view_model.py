"""Base ViewModel - MVVM Pattern Base Class"""
from typing import Callable, List, Any, Optional
from abc import ABC


class BaseViewModel(ABC):
    """
    Base class for all ViewModels in MVVM pattern

    Provides:
    - Observable pattern for property changes
    - Event subscription mechanism
    - Common ViewModel functionality
    """

    def __init__(self):
        """Initialize base view model"""
        self._property_changed_callbacks: List[Callable[[str, Any], None]] = []
        self._event_handlers: dict = {}

    def subscribe_property_changed(self, callback: Callable[[str, Any], None]) -> None:
        """
        Subscribe to property change notifications

        Args:
            callback: Function called when any property changes (property_name, new_value)
        """
        self._property_changed_callbacks.append(callback)

    def _notify_property_changed(self, property_name: str, value: Any) -> None:
        """
        Notify all subscribers that a property has changed

        Args:
            property_name: Name of the changed property
            value: New value of the property
        """
        for callback in self._property_changed_callbacks:
            try:
                callback(property_name, value)
            except Exception as e:
                print(f"Error in property changed callback: {e}")

    def subscribe_event(self, event_name: str, callback: Callable) -> None:
        """
        Subscribe to a named event

        Args:
            event_name: Name of the event
            callback: Function to call when event is raised
        """
        if event_name not in self._event_handlers:
            self._event_handlers[event_name] = []
        self._event_handlers[event_name].append(callback)

    def _raise_event(self, event_name: str, *args, **kwargs) -> None:
        """
        Raise an event to all subscribers

        Args:
            event_name: Name of the event
            *args, **kwargs: Arguments to pass to event handlers
        """
        if event_name in self._event_handlers:
            for handler in self._event_handlers[event_name]:
                try:
                    handler(*args, **kwargs)
                except Exception as e:
                    print(f"Error in event handler for '{event_name}': {e}")
