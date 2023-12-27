import collections
import logging

logger = logging.getLogger(__name__)

class EventBus:
    _events = collections.defaultdict(list)  # Dictionary to store event listeners

    @classmethod
    def on(cls, key: str, listener: callable):
        """Register a listener for an event with the given key."""
        cls._events[key].append(listener)

    @classmethod
    def remove(cls, key: str, listener: callable = None):
        """Remove a listener for an event with the given key or listener."""
        if listener:
            cls._events[key].remove(listener)
        else:
            cls._events.pop(key, None)

    @classmethod
    def fire(cls, key: str, data: dict = None):
        """Fire an event with the given key."""
        for listener in cls._events.get(key, []):
            try:
                listener(data)
            except Exception as e:
                logger.error(f"Error firing event {key}", e)

    @classmethod
    def clear(cls):
        """Clear all registered events."""
        cls._events.clear()
