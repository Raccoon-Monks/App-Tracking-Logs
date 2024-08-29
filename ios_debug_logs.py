import sys
from platforms_ios import firebase_ios, universal_analytics_ios, appsflyer
from interface import show_program_finished, show_error_message, show_custom_message
from tools import ui_data, utils


if __name__ == "__main__":
    operating_system = ui_data.OperatingSystem()
    platforms = ui_data.Platform()
    enabled_platforms = [
        platforms.GA4,
        platforms.APPSFLYER
    ]

    instructions = ui_data.Instructions(operating_system.IOS, enabled_platforms)
    

    args, platform = utils.get_arguments_and_option(instructions)
    platforms = ui_data.Platform()

    no_argument: bool = True if (len(sys.argv) == 1) else False

    try:
        match (platform):
            case platforms.GA4:
                if (no_argument) or (args.pattern1 == None and args.pattern2 == None): # Only -v exists in the call
                    firebase_ios.get_event_log(number_arguments=0)
                
                elif args.pattern1 != None and args.pattern2 != None:
                    firebase_ios.get_event_log(number_arguments=2, pattern1=args.pattern1, pattern2=args.pattern2)
                
                elif args.pattern1 != None or args.pattern2 != None:
                    term = args.pattern1 if args.pattern1 != None else args.pattern2
                    firebase_ios.get_event_log(number_arguments=1, pattern1=term)

            case platforms.GAU:
                universal_analytics_ios.no_arguments() if (no_argument) else universal_analytics_ios.with_arguments(args)

            case platforms.APPSFLYER:
                appsflyer.appsflyer()

            case platforms.ADJUST | platforms.SINGULAR | platforms.GTM:
                show_custom_message(f"{ui_data.Icon.LOCK.value} {ui_data.Error.NO_SUPORT.value}")
                sys.exit(0)

            case ui_data.Option.QUIT.value:
                show_program_finished()
                sys.exit(0)

            case _:
                show_error_message(ui_data.Error.CHOICE_OPTION.value)

    except Exception as error:
        show_error_message(str(error))
