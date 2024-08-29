from os import system, name as os_name
from tools import ui_data

colors = ui_data.Colors()


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


def show_blocking_message(text: str) -> None:
    if len(text) != 0:
        print(f"{ui_data.Icon.LOCK.value} {text}")
    else:
        print()


def show_log(log: str) -> None:
    print(f"{log}")


def show_program_finished():
    print(f"\n{colors.LIGHT_GRAY}{ui_data.Message.PROGRAM_FINISHED.value}{colors.CLOSE} {ui_data.Icon.RACCOON.value}")
    

if __name__ == "__main__":
    clear_screen()
    title("Debug Logs")
    options(["platform A", "platform B", "platform C"], "", "")
    show_custom_message("This is a test.")
    