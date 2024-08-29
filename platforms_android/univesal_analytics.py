import io
import re
import subprocess
import sys
import argparse
from tools import ui_data, utils
from interface import show_log, show_error_message

colors = ui_data.Colors()


def enable_verbose_logging() -> subprocess.Popen:
    """Enable verbose logging mode.

    Returns:
        proc (subprocess.Popen): Instance of the Popen class. 
    """
    try:
        subprocess.run(utils.COMMAND.ENABLE_GAU_DEBUG_ANDROID.value.split(" "))
        proc = subprocess.Popen(utils.COMMAND.FILTER_GAV4_SVC.value.split(" "), stdout=subprocess.PIPE)
    except Exception as error:
        show_error_message(ui_data.Error.ENABLE_VERBOSE_ANDROID.value, possible_cause=str(error))
        sys.exit(1)
    else:
        return proc


def no_arguments() -> None:
    """Shows event tags and screenview tags being saved to the database. That is, these hits will still be sent later.
    """
    proc = enable_verbose_logging()

    re_hit_saved = re.compile(r'Hit\ saved\ to\ database')
    re_event = re.compile(r't=event')
    re_screenview = re.compile(r't=screenview')

    for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
        if re_hit_saved.search(line):
            line = re.sub(r', ', r'\n', line)
            if re_event.search(line):
                show_log(f"{colors.YELLOW}{line}{colors.CLOSE}")
            elif re_screenview.search(line):
                show_log(f"{colors.BLUE}{line}{colors.CLOSE}")


def with_arguments(args: argparse.Namespace) -> None:
    """Filters the logs/records based on arguments given by the user.

    Args:
        args (argparse.Namespace): Arguments passed by the user in the call to execute the script.
    """
    if args.pattern1 == None and args.pattern2 == None: # Only -v exists in the call
        no_arguments()

    elif args.pattern1 != None and args.pattern2 != None:
        proc = enable_verbose_logging()
        re_terms = re.compile(rf"{args.pattern1}|{args.pattern2}")

        for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
            check_terms = list(set(re_terms.findall(line, re.IGNORECASE)))
            
            if len(check_terms) == 2:
                check_terms.sort() # sort - alphabetically
                line = re.sub(r',\ ', r'\n', line)
                line = re.sub(f"{check_terms[0]}", f"{colors.BLUE}{check_terms[0]}{colors.CLOSE}", line)
                line = re.sub(f"{check_terms[1]}", f"{colors.GREEN}{check_terms[1]}{colors.CLOSE}", line)
                show_log(line)
    
    elif args.pattern1 != None or args.pattern2 != None:
        proc = enable_verbose_logging()
        term = args.pattern1 if args.pattern1 != None else args.pattern2
        re_terms = re.compile(rf"{term}")

        for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
            term_match = re_terms.search(line, re.IGNORECASE)
            if term_match:
                line = re.sub(r', ', r'\n', line)
                line = re.sub(term_match.group(), f"{colors.BLUE}{term_match.group()}{colors.CLOSE}", line)
                show_log(line)
