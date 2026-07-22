"""Thread-local context describing which capture is currently running.

The web server starts each capture in its own thread and sets the operating
system / platform here before the capture loop begins. ``interface.show_log``
reads it to tag every published event, so the browser knows where each event
came from. In the plain CLI the context is simply unset (values are ``None``).

Standard library only.
"""

import threading

_ctx = threading.local()


def set_context(operating_system: str, platform: str) -> None:
    """Set the operating system / platform for the current thread."""
    _ctx.operating_system = operating_system
    _ctx.platform = platform


def get_context() -> "tuple[str | None, str | None]":
    """Return ``(operating_system, platform)`` for the current thread.

    Both values are ``None`` when no context has been set (e.g. plain CLI use).
    """
    return (
        getattr(_ctx, "operating_system", None),
        getattr(_ctx, "platform", None),
    )
