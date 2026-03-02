import threading
import logging
from typing import Callable

logger = logging.getLogger(__name__)


class Debouncer:
    """
    Ensures a callback fires only once per file after a quiet period.
    Each new event for the same key resets the timer.
    """

    def __init__(self, wait: float = 0.5):
        self.wait = wait                        # seconds to wait after last event
        self._timers: dict[str, threading.Timer] = {}
        self._lock = threading.Lock()           # thread-safe access to _timers

    def call(self, key: str, callback: Callable, *args, **kwargs):
        with self._lock:
            # Cancel existing timer for this key if one is running
            if key in self._timers:
                self._timers[key].cancel()
                logger.debug(f"[DEBOUNCE] Reset timer for: {key}")

            # Start a fresh timer
            timer = threading.Timer(
                self.wait,
                self._fire,
                args=[key, callback, args, kwargs]
            )
            self._timers[key] = timer
            timer.start()

    def _fire(self, key: str, callback: Callable, args, kwargs):
        with self._lock:
            self._timers.pop(key, None)  # clean up after firing
        logger.debug(f"[DEBOUNCE] Firing for: {key}")
        callback(*args, **kwargs)

    def cancel_all(self):
        """Clean shutdown — cancel all pending timers."""
        with self._lock:
            for timer in self._timers.values():
                timer.cancel()
            self._timers.clear()