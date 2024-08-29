import io
import re
import subprocess
import json
from tools import utils, ui_data
from interface import show_log

def appsflyer():
    colors = ui_data.Colors()
    command = utils.COMMAND.FILTER_APPSFLYER.value
    print(command)
    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    customer_user_id = re.compile(r'CustomerUserID:')
    send_event = re.compile(r'SEND\ Event')
    event_name = re.compile(r'eventName')
    event_value = re.compile(r'eventvalue')

    for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
        line = re.sub("%22", "\"", line)
        line = re.sub("%7B", "{", line)
        line = re.sub("%7D", "}", line)
        line = re.sub("%2C", ",", line)
        line = re.sub("%5B", "[", line)
        line = re.sub("%5D", "]", line)
        line = re.sub("%20", " ", line)
        if customer_user_id.search(line, re.IGNORECASE):
            line = f"{colors.BLUE}{line}{colors.CLOSE}"
        elif send_event.search(line, re.IGNORECASE):
            line = f"{colors.BLUE}{line}{colors.CLOSE}"
        elif event_name.search(line, re.IGNORECASE):
            line = re.sub("eventName", f"{colors.BLUE}eventName{colors.YELLOW}", line)
            line = re.sub("eventvalue", f"{colors.BLUE}eventvalue{colors.YELLOW}", line)
            line = re.sub("appUID", f"{colors.BLUE}appUID{colors.YELLOW}", line)
            line =f"{colors.YELLOW}{line}{colors.CLOSE}"
        else:
            line = f"{colors.LIGHT_GRAY}{line}{colors.CLOSE}"
            
        show_log(line)
