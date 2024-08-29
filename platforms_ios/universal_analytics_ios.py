import io
import re
import subprocess
import sys
import argparse
from tools import ui_data, utils
from interface import show_log, show_error_message


def enable_verbose_logging() -> subprocess.Popen:
    """Enable simulator or device debug logs.

    Returns:
        proc (subprocess.Popen): Instance of the Popen class. 
    """
    try:
        proc = subprocess.Popen(utils.COMMAND.ENABLE_GAU_DEBUG_IOS.value, shell=True, stdout=subprocess.PIPE)

    except Exception as error:
        show_error_message(ui_data.Error.ENABLE_VERBOSE_IOS.value, possible_cause=str(error))
        sys.exit(1)

    else:
        return proc


def no_arguments() -> None:
    """Shows event tags and screenview tags being saved to the database. That is, these hits will still be sent later.
    """
    colors = ui_data.Colors()
    proc = enable_verbose_logging()
    
    re_hit_saved = re.compile(r"GoogleAnalytics.*Saved\ hit")
    re_event = re.compile(r"parameters\ =.*\ event")
    re_screenview = re.compile(r"screenview")
    new_event = re.compile(r"\d\d:\d\d:\d\d.\d\d.*0x")
    continue_log = False
    event_log = ""

    for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
        if continue_log == True and not new_event.search(line, re.IGNORECASE):
            event_log += line

        elif re_hit_saved.search(line, re.IGNORECASE) and continue_log == False:
            event_log += line
            continue_log = True
        
        else:
            if re_hit_saved.search(event_log, re.IGNORECASE):
                event_log = re.sub(r"0x.*Saved\ hit", r"Google Analytics - Saved hit", event_log)
                single_line_record = re.sub("\n", r"", event_log)
                continue_log = False
                
                if re_event.search(single_line_record, re.IGNORECASE):
                    show_log(f"{colors.YELLOW}{event_log}{colors.CLOSE}")

                elif re_screenview.search(single_line_record, re.IGNORECASE):
                    show_log(f"{colors.BLUE}{event_log}{colors.CLOSE}")

                event_log = ""


def with_arguments(args: argparse.Namespace):
    """Filters the logs/records based on arguments given by the user.

    Args:
        args (argparse.Namespace): Arguments passed by the user in the call to execute the script.
    """
    colors = ui_data.Colors()
    
    if args.pattern1 == None and args.pattern2 == None: # Only -v exists
        no_arguments()

    elif args.pattern1 != None and args.pattern2 != None:
        proc = enable_verbose_logging()

        re_hit_saved = re.compile(r"GoogleAnalytics.*Saved\ hit")
        re_terms = re.compile(rf"{args.pattern1}|{args.pattern2}")
        continue_log = False
        new_event = re.compile(r"\d\d:\d\d:\d\d.\d\d.*0x")
        event_log = ""

        for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
            if continue_log == True and not new_event.search(line, re.IGNORECASE):
                event_log += line

            elif re_hit_saved.search(line, re.IGNORECASE) and continue_log == False:
                event_log += line
                continue_log = True

            else:
                if re_hit_saved.search(event_log, re.IGNORECASE):
                    event_log = re.sub(r"0x.*Saved\ hit", r"Google Analytics - Saved hit", event_log)

                    continue_log = False
                    
                    check_terms = list(set(re_terms.findall(event_log, re.IGNORECASE)))
            
                    if len(check_terms) == 2:
                        check_terms.sort() # sort - alphabetically

                        event_log = re.sub(f"{check_terms[0]}", f"{colors.GREEN}{check_terms[0]}{colors.CLOSE}", event_log)
                        event_log = re.sub(f"{check_terms[1]}", f"{colors.BLUE}{check_terms[1]}{colors.CLOSE}", event_log)
                        show_log(event_log)
                        
                    event_log = ""
    
    elif args.pattern1 != None or args.pattern2 != None:
        proc = enable_verbose_logging()
        term = args.pattern1 if args.pattern1 != None else args.pattern2
        re_terms = re.compile(rf"{term}")

        re_hit_saved = re.compile(r"GoogleAnalytics.*Saved\ hit")
        continue_log = False
        new_event = re.compile(r"\d\d:\d\d:\d\d.\d\d.*0x")
        event_log = ""

        for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
            if continue_log == True and not new_event.search(line, re.IGNORECASE):
                event_log += line

            elif re_hit_saved.search(line, re.IGNORECASE) and continue_log == False:
                event_log += line
                continue_log = True
            
            else:
                if re_hit_saved.search(event_log, re.IGNORECASE):
                    event_log = re.sub(r"0x.*Saved\ hit", r"Google Analytics - Saved hit", event_log)

                    continue_log = False                
                    match = re_terms.search(event_log, re.IGNORECASE)
                    if match:
                        # event_log = re.sub(r', ', r'\n', line)
                        event_log = re.sub(match.group(), f"{colors.GREEN}{match.group()}{colors.CLOSE}", event_log)
                        show_log(event_log)

                    event_log = ""


if __name__ == "__main__":
    no_arguments()
