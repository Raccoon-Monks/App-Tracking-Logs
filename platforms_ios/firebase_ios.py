import io
import re
import subprocess
import sys
from tools import ui_data, utils
from interface import show_log, show_error_message

colors = ui_data.Colors()


def enable_verbose_logging() -> subprocess.Popen:
    """Enable simulator or device debug logs.

    Returns:
        proc (subprocess.Popen): Instance of the Popen Class.
    """
    try:
        proc = subprocess.Popen(utils.COMMAND.GET_FIREBASE_LOG_IOS.value, shell=True, stdout=subprocess.PIPE)
    except Exception as error:
        show_error_message(ui_data.Error.ENABLE_VERBOSE_IOS.value, possible_cause=str(error))
        sys.exit(1)
    else:
        return proc


def get_event_log(number_arguments: int = 0, pattern1:str = None, pattern2:str = None) -> None:
    """Captures events that are being logged by the Firebase SDK.

    Args:
        number_arguments (int, optional): Number of arguments passed in the call to execute the script. Defaults to 0.
        pattern1 (str, optional): First search term/correspondence. Defaults to None.
        pattern2 (str, optional): Second search term/correspondence. Defaults to None.
    """
    proc = enable_verbose_logging()
    
    re_capture_bundle = re.compile(r"Logging\ event")
    new_event = re.compile(r"\d\d:\d\d:\d\d.\d\d.*0x")
    continue_log = False
    event_log = ""

    for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
        if continue_log == True and not new_event.search(line, re.IGNORECASE):
            event_log += line

        elif re_capture_bundle.search(line, re.IGNORECASE) and continue_log == False:
            event_log += line
            continue_log = True
        
        else:
            if re_capture_bundle.search(event_log, re.IGNORECASE):
                continue_log = False
                event_log = re.sub(r"0x.*event:\ ", r"", event_log)

                # print the logged events
                if number_arguments == 0:
                    print_default(event_log)
                elif number_arguments == 1:
                    print_single_argument(event_log, pattern1)
                else: # 2
                    print_double_argument(event_log, pattern1, pattern2)

                event_log = ""


def print_default(event_log: str) -> None:
    """Print the logged events (without arguments passed in the script call).

    Args:
        event_log (str): event logged by the Firebase SDK.
    """
    e_screenview = re.compile(r'name.*screen_view')
    e_auto = re.compile(r'origin.*auto')
    
    if e_screenview.search(event_log) and not e_auto.search(event_log):
        show_log(f"{colors.BLUE}{event_log}{colors.CLOSE}")

    elif e_auto.search(event_log):
        show_log(f"{colors.LIGHT_GRAY}{event_log}{colors.CLOSE}")

    else:
        show_log(f"{colors.YELLOW}{event_log}{colors.CLOSE}")
    

def print_single_argument(event_log:str, pattern1:str) -> None:
    """Print the logged events (with an argument passed in the script call).

    Args:
        event_log (str): event logged by the Firebase SDK.
        pattern1 (str): search term or match term used in the filter.
    """
    re_terms = re.compile(rf"{pattern1}")
    match = re_terms.search(event_log, re.IGNORECASE)

    if match:
        event_log = re.sub(match.group(), f"{colors.GREEN}{match.group()}{colors.CLOSE}", event_log)
        show_log(event_log)


def print_double_argument(event_log:str, pattern1:str, pattern2:str) -> None:
    """Print the logged events (with two arguments passed in the script call).

    Args:
        event_log (str): event logged by the Firebase SDK.
        pattern1 (str): First search term/correspondence.
        pattern2 (str): Second search term/correspondence.
    """
    re_terms = re.compile(rf"{pattern1}|{pattern2}")
    check_terms = list(set(re_terms.findall(event_log, re.IGNORECASE)))

    if len(check_terms) == 2:
        check_terms.sort() # sort - alphabetical order
        event_log = re.sub(f"{check_terms[0]}", f"{colors.GREEN}{check_terms[0]}{colors.CLOSE}", event_log)
        event_log = re.sub(f"{check_terms[1]}", f"\{colors.BLUE}{check_terms[1]}{colors.CLOSE}", event_log)
        
        show_log(event_log)
