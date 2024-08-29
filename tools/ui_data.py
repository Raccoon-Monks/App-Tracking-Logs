from dataclasses import dataclass, field
from enum import Enum


@dataclass
class Colors:
    BLUE: str = "\033[0;34m"
    GREEN: str = "\033[0;32m"
    YELLOW: str = "\033[0;33m"
    LIGHT_GRAY: str = "\033[0;90m"
    RED: str = "\033[31m"
    CLOSE: str = "\033[m"
    _document_url: str = field(init=False, repr=False)


    def __post_init__(self) -> None:
        self._document_url = "https://github.com/shiena/ansicolor/blob/master/README.md"


@dataclass
class Instructions:
    _operating_system: str
    _platform_options: list[str] = field(default_factory=list)
    title: str = field(init=False, repr=False)


    def __post_init__(self):
        self.title = f"Debug Logs - {self._operating_system}"
        if (len(self._platform_options) == 0):
            platforms = Platform()
            self._platform_options = [
                platforms.GA4,
                platforms.GAU,
                platforms.APPSFLYER,
                platforms.ADJUST,
                platforms.SINGULAR,
                platforms.GTM
            ]
        
        self._platform_options.append(Option.QUIT.value)


    @property
    def general_intruction_text(self) -> str:
         key = "Control" if self._operating_system == OperatingSystem.IOS else "CTRL"
         return f"After choosing the platform and \nthe logs are being displayed, to \nstop press '{key} + C'."


    @property
    def more_details_text(self) -> str:
        colors = Colors()

        return f"Use this script to immediately observe \nthe triggering of events, helping you \nto verify that events are being sent. \nThe script only enables detailed \nlogging, allowing you to check that \nevents are being logged correctly by \nthe SDK. This includes both manually \nand automatically logged events.\n\nColor pattern: \n\t{colors.BLUE}blue log{colors.CLOSE} - screenview \n\t{colors.YELLOW}yellow log{colors.CLOSE} - event \n\t{colors.LIGHT_GRAY}gray log{colors.CLOSE} - automatic\n"
    
    
    @property
    def error_message_option(self) -> str:
        colors = Colors()

        platform_options_index = [str(x) for x in range(len(self._platform_options))]
        options_list_text = f"{', '.join(platform_options_index[:-1])} or {platform_options_index[-1]}"
        message = f"{colors.RED}Invalid option. Choose between {options_list_text}.{colors.CLOSE}"

        return message
    

    @property
    def platform_option_indexes(self) -> list[str]:

        return [str(x) for x in range(len(self._platform_options))]


@dataclass
class OperatingSystem:
    IOS: str = "iOS"
    ANDROID: str = "Android"
    WINDOWS:str = "WindowsNT"
    Linux: str = "Linux"
    MAC: str = "Darwin"


@dataclass
class Platform:
    GA4: str = "Google Analytics 4"
    GAU: str = "Google Analytics Universal"
    APPSFLYER: str = "AppsFlyer"
    ADJUST: str = "Adjust"
    SINGULAR: str = "Singular"
    GTM: str = "Google Tag Manager"


class Icon(Enum):
    DETECTIVE = "\U0001F575"
    MOBILE_PHONE = "\U0001F4F1"
    LOCK = "\U0001F512"
    OPEN_LOCK = "\U0001F513"
    RACCOON = "\U0001F99D"
    POLICE_CAR_LIGHT = "\U0001F6A8"



class Argument(Enum):
    DESCRIPTION = "Activate detailed logging and immediately see the events being sent. Use arguments to filter events or other information."
    FIRST_PATTERN_FLAG = "-p1"
    SECOND_PATTERN_FLAG = "-p2"
    FIRST_PATTERN_NAME = "--pattern1"
    SECOND_PATTERN_NAME = "--pattern2"
    FIRST_PATTERN_HELP = "The first regular expression pattern."
    SECOND_PATTERN_HELP = "The second regular expression pattern."
    VERBOSE_FLAG = "-v"
    VERBOSE_NAME = "--verbose"
    VERBOSE_HELP = "increase output verbosity"
    VERBOSE_ACTION = "store_true"


class Label(Enum):
    CHOOSE_PLATFORM: str = "Choose the platform:"
    OPTION: str = "Option: "


class Error(Enum):
    CHOICE_OPTION = "Oops. Sorry, an error occurred while choosing the option. Try again."
    ENABLE_VERBOSE_IOS = "Oops. There was an error. Make sure you have a booted device or emulator. Also make sure 'xcrun' is installed."
    ENABLE_VERBOSE_ANDROID = "Oops. There was an error. Make sure 'adb' is installed."
    UNKNOWN = "unknown"
    NO_SUPORT = "Sorry. This option is not yet supported."


class Option(Enum):
    QUIT: str = "Quit"


class Message(Enum):
    PROGRAM_FINISHED = "Program finished."


if __name__ == "__main__":
    print(Colors())
    print(Instructions())