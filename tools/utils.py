from enum import Enum
import argparse
from interface import title, options, clear_screen, show_custom_message
from tools import ui_data

class COMMAND(Enum):
    GET_FIREBASE_LOG_IOS = "xcrun simctl spawn booted log stream --level=debug --predicate \"eventMessage contains 'FirebaseAnalytics'\""
    FA_VERBOSE = "adb shell setprop log.tag.FA VERBOSE"
    FA_SVC_VERBOSE = "adb shell setprop log.tag.FA-SVC VERBOSE"
    GTM_VERBOSE = "adb shell setprop log.tag.GoogleTagManager VERBOSE"
    FILTER_FA_FA_SVC = "adb logcat -v time -s FA FA-SVC"
    FILTER_GAV4_SVC = "adb logcat -v time -s GAv4-SVC"
    FILTER_GTM = "adb logcat -v time -s GoogleTagManager"
    ENABLE_GAU_DEBUG_IOS = "xcrun simctl spawn booted log stream --level=debug --predicate \"eventMessage contains 'GoogleAnalytics'\""
    ENABLE_GAU_DEBUG_ANDROID = "adb shell setprop log.tag.GAv4-SVC DEBUG"
    FILTER_APPSFLYER = "xcrun simctl spawn booted log stream --level=debug --predicate \"eventMessage contains 'com.appsflyer' or eventMessage contains 'CustomerUserID'\""
    LAUNCH_APP = "xcrun simctl launch <device> <bundle> <arguments>"
    # xcrun simctl launch <device> <bundle> <arguments>
    # xcrun simctl install <device> <path>
    # simctl openurl <device> <URL>



def receive_arguments() -> argparse.Namespace:
    """Receives and handles the arguments passed in the call to execute the script.

    Returns:
        [argparse.Namespace]: All arguments received.
    """
    arg = ui_data.Argument

    parser = argparse.ArgumentParser(description=arg.DESCRIPTION.value)
    parser.add_argument(arg.FIRST_PATTERN_FLAG.value, arg.FIRST_PATTERN_NAME.value, type=str, help=arg.FIRST_PATTERN_HELP.value)
    parser.add_argument(arg.SECOND_PATTERN_FLAG.value, arg.SECOND_PATTERN_NAME.value, type=str, help=arg.SECOND_PATTERN_HELP.value)
    parser.add_argument(arg.VERBOSE_FLAG.value, arg.VERBOSE_NAME.value, help=arg.VERBOSE_HELP.value, action=arg.VERBOSE_ACTION.value)

    return parser.parse_args()


def user_choice(instructions, verbose: bool = False) -> str:
    """It displays the platforms (options) and receives the user's choice.

    Args:
        verbose (bool): Determines whether the programme description will be displayed to the user in the platform's choice menu.

    Returns:
        action (str): Index related to the platform option chosen by the user.
    """
    option_index = ""
    error_message = ""

    while option_index not in instructions.platform_option_indexes:  # ['0', '2', '3', ...]
        clear_screen()
        title(instructions.title)
        if verbose:
            show_custom_message(instructions.more_details_text)
        options(instructions._platform_options, instructions.general_intruction_text, error_message)

        option_index = input(ui_data.Label.OPTION.value).strip()
        error_message = instructions.error_message_option
        
    return option_index


def get_arguments_and_option(instructions: ui_data.Instructions) -> tuple[argparse.Namespace, str]:
    args = receive_arguments()
    option_index = user_choice(instructions, True) if args.verbose else user_choice(instructions)
    platform = instructions._platform_options[int(option_index)]

    return args, platform