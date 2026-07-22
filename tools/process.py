"""Central spawning of the capture subprocesses (adb / xcrun simctl).

The platform modules use :func:`spawn` instead of calling ``subprocess.Popen``
directly. This keeps a registry of the live capture processes so the web UI can
stop or switch the capture via :func:`terminate_all`.

On POSIX each process is started in its own session (``start_new_session``) so
that shell-launched children (``simctl ... log stream``) are terminated together
with the shell via ``killpg``.

Standard library only.
"""

import os
import signal
import subprocess
import threading

_procs: "list[subprocess.Popen]" = []
_lock = threading.Lock()


def spawn(command, shell: bool = False) -> subprocess.Popen:
    """Start a capture subprocess with its stdout piped, and register it.

    Args:
        command: Command to run. A list of args when ``shell`` is ``False``, or
            a shell string when ``shell`` is ``True``.
        shell (bool): Whether to run the command through the shell.

    Returns:
        subprocess.Popen: The started process (stdout is a pipe).
    """
    kwargs = {"stdout": subprocess.PIPE, "shell": shell}
    if os.name != "nt":
        # New session -> we can kill the whole process group (shell + children).
        kwargs["start_new_session"] = True

    proc = subprocess.Popen(command, **kwargs)
    with _lock:
        _procs.append(proc)
    return proc


def terminate_all() -> None:
    """Terminate every registered capture process and clear the registry."""
    with _lock:
        procs = list(_procs)
        _procs.clear()

    for proc in procs:
        _terminate(proc)


def _terminate(proc: subprocess.Popen) -> None:
    """Best-effort termination of a single process (and its group on POSIX)."""
    if proc.poll() is not None:
        return
    try:
        if os.name != "nt":
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        else:
            proc.terminate()
    except (ProcessLookupError, PermissionError, OSError):
        try:
            proc.terminate()
        except OSError:
            pass
