import io
import re
import subprocess
import sys
import argparse
import json
from tools import ui_data, utils
from interface import show_log, show_error_message


def enable_verbose_logging(FA_verbose: bool = False) -> subprocess.Popen:
    """Enable verbose logging mode.

    Args:
        FA_verbose (bool, optional): Enables FA Verbose. Defaults to False.

    Returns:
        proc (subprocess.Popen): Instance of the Popen class. 
    """
    try:
        if FA_verbose:
            subprocess.run(utils.COMMAND.FA_VERBOSE.value.split(" "))

        subprocess.run(utils.COMMAND.FA_SVC_VERBOSE.value.split(" "))
        proc = subprocess.Popen(utils.COMMAND.FILTER_FA_FA_SVC.value.split(" "), stdout=subprocess.PIPE)
    except Exception as error:
        show_error_message(ui_data.Error.ENABLE_VERBOSE_ANDROID.value, possible_cause=str(error))
        sys.exit(1)
    else:
        return proc


def edit_log(log: str) -> str:
    """Edits the log to better organize key values.

    Args:
        log (str): log/record to be edited.

    Returns:
        log (str): edited log/record.
    """
    re_event_params = re.compile(r"Bundle\[\{")

    if re_event_params.search(log, re.IGNORECASE):
        try:
            new_log: str = ""
            event_name, params = log.split(",params=")
            
            event_name = re.sub(r", |,", r"\n", event_name)
            event_name = re.sub(r"V/FA-SVC.*\):\ ", r"", event_name)
            params = re.sub(r"Bundle\[\{", r'{"', params)
            params = re.sub(r"}]", r'"}', params)
            params = re.sub(r", ", r'", "', params)
            params = re.sub(r"=", r'": "', params)
            params = re.sub(r'"{', r'{', params)
            params = re.sub(r'"\[', r'[', params)
            params = re.sub(r'}"', r'}', params)
            params = re.sub(r']"', r']', params)
            params_json = json.loads(params, parse_float=str)

            new_log = f"{event_name} \nparams = {json.dumps(params_json, indent=4)}\n".replace('\"', '')

        except Exception as error:
             # an error case: passing event to registered event handler
            log = re.sub(r"\w+\[\{", r"Bundle[{\n", log)
            log = re.sub(r"\}\]", r"\n}]", log)
            log = re.sub(r", |,", r"\n", log)

        else:
            log = new_log

    return log

"""
# RAFAEL
def askIfList():
    viewItemListEnabled = True
    query = input("Do you want to show lists events? (N/n) for no, any other input for yes.")

    if query == "N" or query == "n":
        viewItemListEnabled = False

    return viewItemListEnabled"""


def no_arguments() -> None:
    """Displays logs of events being logged. 
    """
    colors = ui_data.Colors()
    proc = enable_verbose_logging()

    re_registered_event = re.compile(r"Logging\ event:")
    screenview_event = re.compile(r'name=screen_view|name\ =\ screen_view')
    # viewItemList_event = re.compile(r'name=view_item_list| name\ =\ view_item_list') # RAFAEL
    automatic_event = re.compile(r'origin=auto|origin\ =\ auto')

    # viewItemListEnabled = True #

    # viewItemListEnabled = askIfList()

    for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):

        if re_registered_event.search(line, re.IGNORECASE):
            line = edit_log(line)

            """if viewItemList_event.search(line): 
                if viewItemListEnabled:
                    print(f"{colors.RED}{line}{colors.CLOSE}")""" # RAFAEL

            if screenview_event.search(line) and not automatic_event.search(line):
                show_log(f"{colors.BLUE}{line}{colors.CLOSE}")

            elif automatic_event.search(line):
                show_log(f"{colors.LIGHT_GRAY}{line}{colors.CLOSE}")
            else:
                show_log(f"{colors.YELLOW}{line}{colors.CLOSE}")


def with_arguments(args: argparse.Namespace) -> None:
    """Filters the logs/records based on arguments given by the user.

    Args:
        args (argparse.Namespace): Arguments passed by the user in the call to execute the script.
    """
    if args.pattern1 == None and args.pattern2 == None: # Only -v exists in the call
        no_arguments()

    elif args.pattern1 != None and args.pattern2 != None:
        colors = ui_data.Colors()
        proc = enable_verbose_logging(FA_verbose=True)
        re_terms = re.compile(rf"{args.pattern1}|{args.pattern2}")

        for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
            check_terms = list(set(re_terms.findall(line, re.IGNORECASE)))
            
            if len(check_terms) == 2:
                check_terms.sort() # sort - alphabetically
                line = edit_log(line)

                line = re.sub(f"{check_terms[0]}", f"{colors.BLUE}{check_terms[0]}{colors.CLOSE}", line)
                line = re.sub(f"{check_terms[1]}", f"{colors.GREEN}{check_terms[1]}{colors.CLOSE}", line)
                show_log(line)

    elif args.pattern1 != None or args.pattern2 != None:
        colors = ui_data.Colors()
        proc = enable_verbose_logging(FA_verbose=True)
        term = args.pattern1 if args.pattern1 != None else args.pattern2
        re_terms = re.compile(rf"{term}")
        
        for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
            term_match = re_terms.search(line, re.IGNORECASE)         
            if term_match:
                line = edit_log(line)
                line = re.sub(term_match.group(), f"{colors.BLUE}{term_match.group()}{colors.CLOSE}", line)
                show_log(line)


def view_user_property():
    colors = ui_data.Colors()
    proc = enable_verbose_logging()

    re_set_user_property = re.compile("Setting\ user\ property:")
    re_user_property_removed = re.compile("User\ property\ removed:")

    for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
        if re_set_user_property.search(line, re.IGNORECASE):
            line = re.sub(r"V\/FA.*user\ property:", "Setting user property:\n", line)
            show_log(f"{colors.YELLOW}{line}{colors.CLOSE}")

        elif re_user_property_removed.search(line, re.IGNORECASE):
            line = re.sub(r"D\/FA.*property\ removed", "User property removed", line)
            show_log(f"{colors.LIGHT_GRAY}{line}{colors.CLOSE}")


if __name__ == "__main__":
    no_arguments()