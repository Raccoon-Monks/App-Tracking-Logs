import io
import re
import subprocess
from tools import ui_data, utils
from interface import show_log


def edit_log_firing_tag(log) -> tuple[str, str]:
    """Edits the log to better organize key values.

    Args:
        log (str): log/record to be edited.

    Returns:
        log (str): edited log/record.
        color (str): color to print the log.
    """
    colors = ui_data.Colors()
    re_caputre_screenview = re.compile(r"vtp_trackType=TRACK_SCREENVIEW")
    re_capture_event = re.compile(r"vtp_trackType=TRACK_EVENT")
    color = colors.LIGHT_GRAY
    if re_capture_event.search(log, re.IGNORECASE):
        color = colors.YELLOW
    elif re_caputre_screenview.search(log, re.IGNORECASE):
        color = colors.BLUE

    log = re.sub(r"V.*tag\ Properties: \{", "GTM Executing firing tag Properties: {\n  ", log)
    log = re.sub(r",\ vtp_", "\n  vpt_", log)
    log = re.sub(r"\},\ \{", "},\n    {", log)
    log = re.sub(r"dimension=\[\{", "dimension=[{\n    ", log)
    log = re.sub(r",\ function=", "\n  function=", log)
    log = re.sub(r",\ tag_id=", "\n  tag_id=", log)
    
    return log, color


def main():
    """Print the triggered tags.
    """
    colors = ui_data.Colors()

    subprocess.run(utils.COMMAND.GTM_VERBOSE.value.split(" "))
    proc = subprocess.Popen(utils.COMMAND.FILTER_GTM.value.split(" "), stdout=subprocess.PIPE)

    re_firing_tag = re.compile(r"Executing\ firing\ tag")
    # Remember to add trigger impressions as well.
    # re_evaluating_trigger = re.compile(r"Evaluating\ trigger\ Positive\ predicates")

    for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
        if re_firing_tag.search(line):
            line, color = edit_log_firing_tag(line)
            if color == colors.BLUE:
                show_log(f"{colors.BLUE}{line}{colors.CLOSE}")
            elif color == colors.YELLOW:
                show_log(f"{colors.YELLOW}{line}{colors.CLOSE}")
            else:
                show_log(f"{colors.LIGHT_GRAY}{line}{colors.CLOSE}")


if __name__ == "__main__":
    main()