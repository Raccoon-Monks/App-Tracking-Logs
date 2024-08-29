import io
import re
import subprocess
import json
from tools import ui_data
from interface import show_error_message, show_log


def edit_log(log: str, is_data: bool = False):
    """Edits the log to better organize key values.

    Args:
        log (str): log/record to be edited.

    Returns:
        log (str): edited log/record.
    """
    colors = ui_data.Colors()
    log = re.sub(r',\"prev_event\":.*', "}", log)
    # log = re.sub(r'\"', "'", log)
    log = re.sub(r'\\', "", log)
    log = re.sub(r'\":', "\": ", log)
    log = re.sub(r',', ", ", log)
    log = re.sub(r'\"\{', "{", log)
    log = re.sub(r'\}\"', "}", log)

    try:
        if is_data:
            tag, data = log.split(" data: ")
            data_json = json.loads(data)
            keys_delete = [
                "isFirstCall",
                "registeredUninstall",
                "cell",
                "operator",
                "network",
                "af_v2",
                "sig",
                "isGaiWithGps",
                "lang_code",
                "installDate",
                "dim",
                "app_version_code",
                "firstLaunchDate",
                "device",
                "kef776f",
                "model",
                "brand",
                "last_boot_time",
                "deviceData",
                "date2",
                "date1",
                "counter",
                "af_v",
                "carrier",
                "disk",
                "iaecounter",
                "sc_o",
                "isGaidWithGps"
                ]
            
            for key in keys_delete:
                if key in data_json:
                    del data_json[key]
            
            tag_list = tag.split(" ")
            new_tag = f"{tag_list[0]} {tag_list[1]} AppsFlyer: {tag_list[3]} {tag_list[4]} preparing data (simplified):"
            log = f"{new_tag} \n{json.dumps(data_json, indent=4)}\n"

            if ("eventName" in log) and ("eventValue" in log):
                log = re.sub("eventName", f"{colors.YELLOW}eventName{colors.BLUE}", log)
                log = re.sub(r"event(v|V)alue", f"{colors.YELLOW}eventValue{colors.BLUE}", log)

    except Exception as error:
        show_error_message(str(error))

    return log


def appsflyer_logs():
    """Print events logged by the AppsFlyer SDK.
    """
    colors = ui_data.Colors()
    proc = subprocess.Popen("adb logcat -v time".split(" "), stdout=subprocess.PIPE)

    appf_flyer_log = re.compile(r'AppsFlyer')
    url_request = re.compile(r'url.*inapps.appsflyer.com')
    response_code = re.compile(r'response\ code')
    set_customer_user_Id = re.compile(r'setCustomerUserId')
    event_data = re.compile(r'data:\ \{')
    simpleLog: bool = False

    for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):

        if appf_flyer_log.search(line, re.IGNORECASE):
            if url_request.search(line, re.IGNORECASE):
                show_log(f"{colors.LIGHT_GRAY}{line} {colors.CLOSE}")

            elif event_data.search(line, re.IGNORECASE):
                show_log(f"{colors.BLUE}{edit_log(line, True)} {colors.CLOSE}")

            elif response_code.search(line, re.IGNORECASE):
                show_log(f"{colors.LIGHT_GRAY}{line} \n<{'~+' * 20}~> {colors.CLOSE}")
                
            elif set_customer_user_Id.search(line, re.IGNORECASE):
                show_log(f"{colors.GREEN}{line} {colors.CLOSE}")


if __name__ == "__main__":
    appsflyer_logs()