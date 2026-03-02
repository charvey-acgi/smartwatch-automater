import time
import pytest
from smartwatch.debouncer import Debouncer


def test_fires_once_after_quiet_period():
    """Multiple rapid events should only trigger one callback."""
    call_count = 0

    def callback():
        nonlocal call_count
        call_count += 1

    d = Debouncer(wait=0.2)
    d.call("file.txt", callback)
    d.call("file.txt", callback)  # resets timer
    d.call("file.txt", callback)  # resets timer again

    time.sleep(0.4)  # wait for debounce to fire

    assert call_count == 1  # fired only once ✅


def test_different_keys_fire_independently():
    """Events for different files should each fire their own callback."""
    results = []

    d = Debouncer(wait=0.2)
    d.call("file1.txt", lambda: results.append("file1"))
    d.call("file2.txt", lambda: results.append("file2"))

    time.sleep(0.4)

    assert "file1" in results
    assert "file2" in results
    assert len(results) == 2  # both fired ✅


def test_cancel_all_prevents_firing():
    """Cancelling all timers should prevent any callbacks from firing."""
    fired = []

    d = Debouncer(wait=0.5)
    d.call("file.txt", lambda: fired.append(True))
    d.cancel_all()  # cancel before timer fires

    time.sleep(0.7)

    assert len(fired) == 0  # nothing fired ✅


def test_timer_resets_on_new_event():
    """A new event within the wait window should delay the callback."""
    fired_at = []

    def callback():
        fired_at.append(time.time())

    d = Debouncer(wait=0.3)
    start = time.time()
    d.call("file.txt", callback)
    time.sleep(0.1)
    d.call("file.txt", callback)  # reset — should fire 0.3s from NOW not from start

    time.sleep(0.5)

    assert len(fired_at) == 1
    # Should have fired ~0.4s after start (0.1s delay + 0.3s wait), not at 0.3s
    assert fired_at[0] - start >= 0.35  # ✅ timer was reset