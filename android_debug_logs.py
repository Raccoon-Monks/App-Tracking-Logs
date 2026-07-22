import sys
import capture_registry
from interface import show_error_message, show_program_finished, show_custom_message
from tools import ui_data, utils


if __name__ == "__main__":
    operating_system = ui_data.OperatingSystem()
    enabled_platforms = capture_registry.enabled_platforms(operating_system.ANDROID)

    instructions = ui_data.Instructions(operating_system.ANDROID, list(enabled_platforms))

    args, platform = utils.get_arguments_and_option(instructions)

    no_argument: bool = True if (len(sys.argv) == 1) else False

    if platform == ui_data.Option.QUIT.value:
        show_program_finished()
        sys.exit(0)

    try:
        capture_registry.dispatch(operating_system.ANDROID, platform, args, no_argument)
    except capture_registry.PlatformNotSupported:
        show_custom_message(f"{ui_data.Icon.LOCK.value} {ui_data.Error.NO_SUPORT.value}")
        sys.exit(0)
    except Exception as error:
        show_error_message(str(error))
        sys.exit(1)
