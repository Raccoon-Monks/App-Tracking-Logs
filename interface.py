import re
import threading
import time
from os import system, name as os_name
from tools import ui_data, event_bus, capture_context

colors = ui_data.Colors()

# Strips ANSI color codes so the web UI shows clean text.
_ANSI_RE = re.compile(r"\033\[[0-9;]*m")
# Leading ANSI color code -> event type, mirroring the terminal color convention.
_TYPE_BY_COLOR = {
    colors.BLUE: "screenview",
    colors.YELLOW: "event",
    colors.LIGHT_GRAY: "automatic",
    colors.GREEN: "highlight",
    colors.RED: "error",
}
_event_seq = 0
_seq_lock = threading.Lock()


def _next_event_id() -> int:
    global _event_seq
    with _seq_lock:
        _event_seq += 1
        return _event_seq


def _publish_event(text: str, event_type: str) -> None:
    """Publish an event to the web bus. Best-effort: never breaks the terminal."""
    try:
        operating_system, platform = capture_context.get_context()
        event_bus.publish({
            "id": _next_event_id(),
            "ts": time.strftime("%H:%M:%S"),
            "os": operating_system,
            "platform": platform,
            "type": event_type,
            "text": text,
        })
    except Exception:
        pass


def title(txt: str) -> None:
    """Prints the title in the menu.

    Args:
        txt (str): Title to be printed.
    """
    print(f"{colors.BLUE}" + "-" * 37, end=f"\n{colors.CLOSE}")
    print(f"{colors.GREEN}{ui_data.Icon.DETECTIVE.value} {ui_data.Icon.MOBILE_PHONE.value} {txt}".center(37), end=f"{colors.CLOSE}\n")
    print(f"{colors.BLUE}" + "-" * 37 + f"{colors.CLOSE}")


def options(platforms: list, genera_instruction: str, error_message: str) -> None:
    """Prints the platforms to be chosen by the user.

    Args:
        platforms (list): list of available platforms.
        msg (str, optional): error message. Defaults to "".
    """
    print(f"{colors.LIGHT_GRAY}{genera_instruction} {colors.CLOSE}\n")
    print(f"{ui_data.Label.CHOOSE_PLATFORM.value}")
    for i, platform in enumerate(platforms):
        print(f"[{i}] - {platform}")

    show_blocking_message(text=error_message)
    

def clear_screen() -> None:
    """Clear the terminal screen.
    """
    system("cls" if os_name == "nt" else "clear")


def show_custom_message(text: str) -> None:
    if len(text) != 0:
        print(f"\n{text}")


def show_error_message(text: str, possible_cause: str = ui_data.Error.UNKNOWN.value) -> None:
    if len(text) != 0:
        print(f"\n{ui_data.Icon.POLICE_CAR_LIGHT.value} {colors.RED}Error:{colors.CLOSE} {text}")
        if (possible_cause != ui_data.Error.UNKNOWN.value):
            print(f"\nPossible cause: {possible_cause}.")
        message = text if possible_cause == ui_data.Error.UNKNOWN.value else f"{text} ({possible_cause})"
        _publish_event(message, "error")


def show_blocking_message(text: str) -> None:
    if len(text) != 0:
        print(f"{ui_data.Icon.LOCK.value} {text}")
    else:
        print()


def show_log(log: str) -> None:
    print(f"{log}")

    # Mirror the event to the web UI (no-op when nobody is subscribed).
    match = re.match(r"(\033\[[0-9;]*m)", log)
    event_type = _TYPE_BY_COLOR.get(match.group(1), "log") if match else "log"
    _publish_event(_ANSI_RE.sub("", log).strip("\n"), event_type)


def show_program_finished():
    print(f"\n{colors.LIGHT_GRAY}{ui_data.Message.PROGRAM_FINISHED.value}{colors.CLOSE} {ui_data.Icon.RACCOON.value}")
    

if __name__ == "__main__":
    clear_screen()
    title("Debug Logs")
    options(["platform A", "platform B", "platform C"], "", "")
    show_custom_message("This is a test.")
    