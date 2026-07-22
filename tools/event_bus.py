"""In-process publish/subscribe bus used to mirror captured events to the web UI.

Every event that goes through ``interface.show_log`` is published here. The web
server (``web_debug_logs.py``) subscribes and streams events to the browser via
Server-Sent Events. When nobody is subscribed (e.g. the plain CLI), publishing is
a cheap no-op, so the terminal behaviour is unchanged.

Standard library only.
"""

import queue
import threading

_subscribers: "list[queue.Queue]" = []
_lock = threading.Lock()


def subscribe(maxsize: int = 2000) -> "queue.Queue":
    """Register a new subscriber and return its queue of events.

    Args:
        maxsize (int): Maximum number of buffered events before the oldest is
            dropped. Protects against a slow browser blocking capture.

    Returns:
        queue.Queue: Queue that will receive published events.
    """
    q: "queue.Queue" = queue.Queue(maxsize=maxsize)
    with _lock:
        _subscribers.append(q)
    return q


def unsubscribe(q: "queue.Queue") -> None:
    """Remove a subscriber previously returned by :func:`subscribe`."""
    with _lock:
        if q in _subscribers:
            _subscribers.remove(q)


def publish(event: dict) -> None:
    """Publish an event to every subscriber. Never raises.

    If a subscriber's queue is full the oldest event is dropped to make room,
    so a slow consumer degrades gracefully instead of stalling capture.
    """
    with _lock:
        subscribers = list(_subscribers)

    for q in subscribers:
        try:
            q.put_nowait(event)
        except queue.Full:
            try:
                q.get_nowait()
                q.put_nowait(event)
            except (queue.Empty, queue.Full):
                pass
