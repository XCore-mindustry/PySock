import unittest
from unittest.mock import MagicMock

from eventbus import EventBus


class TestEventBus(unittest.TestCase):

    def setUp(self):
        self.event_bus = EventBus()

    def test_on_listener_added(self):
        def test_listener():
            pass

        self.event_bus.on("test_event", test_listener)
        self.assertIn(test_listener, self.event_bus._events["test_event"])

    def test_remove_listener(self):
        def test_listener():
            pass

        self.event_bus.on("test_event", test_listener)
        self.event_bus.remove("test_event", test_listener)
        self.assertNotIn(test_listener, self.event_bus._events["test_event"])

    def test_remove_key(self):
        def test_listener():
            pass

        self.event_bus.on("test_event", test_listener)
        self.event_bus.remove("test_event")
        self.assertNotIn("test_event", self.event_bus._events)

    def test_fire_event(self):
        mock_listener = MagicMock()

        self.event_bus.on("test_event", mock_listener)
        self.event_bus.fire("test_event")

        mock_listener.assert_called_once()

    def test_fire_nonexistent_event(self):
        mock_listener = MagicMock()

        self.event_bus.on("test_event", mock_listener)
        self.event_bus.fire("nonexistent_event")

        mock_listener.assert_not_called()

    def test_clear(self):
        def test_listener():
            pass

        self.event_bus.on("test_event", test_listener)
        self.event_bus.clear()
        self.assertNotIn("test_event", self.event_bus._events)


if __name__ == '__main__':
    unittest.main()
