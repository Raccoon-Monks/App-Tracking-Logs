"""Single source of truth mapping (operating system, platform) -> capture.

Both CLI entry points (``android_debug_logs.py`` / ``ios_debug_logs.py``) and the
web server (``web_debug_logs.py``) use this module, so the list of supported
platforms and how each one is captured lives in exactly one place.

Standard library only.
"""

import argparse

from tools import ui_data

_os = ui_data.OperatingSystem()
_platforms = ui_data.Platform()


class PlatformNotSupported(Exception):
    """Raised when a platform is not supported for the given operating system."""


def enabled_platforms(operating_system: str) -> "list[str]":
    """Return the platforms offered for the given operating system.

    Mirrors the menus of the two CLI entry points, so the web UI offers exactly
    the same options.
    """
    if operating_system == _os.ANDROID:
        return [
            _platforms.GA4_EVENTS,
            _platforms.GA4_USER_PROPERTY,
            _platforms.APPSFLYER,
            _platforms.GTM,
        ]
    if operating_system == _os.IOS:
        return [
            _platforms.GA4_EVENTS,
            _platforms.APPSFLYER,
        ]
    return []


def available() -> "dict[str, list[str]]":
    """Return ``{operating_system: [platforms]}`` for the web ``/api/platforms``."""
    return {
        _os.ANDROID: enabled_platforms(_os.ANDROID),
        _os.IOS: enabled_platforms(_os.IOS),
    }


def dispatch(operating_system: str, platform: str,
             args: "argparse.Namespace | None" = None,
             no_argument: bool = True) -> None:
    """Run the capture for ``(operating_system, platform)`` (blocking).

    Args:
        operating_system (str): ``ui_data.OperatingSystem`` value (Android / iOS).
        platform (str): ``ui_data.Platform`` value chosen by the user.
        args (argparse.Namespace | None): CLI filter arguments. When ``None`` a
            no-filter namespace is used (the web always captures the full stream).
        no_argument (bool): ``True`` when the script was called with no filter
            arguments (full stream). Defaults to ``True`` for web callers.

    Raises:
        PlatformNotSupported: When the platform is not available for the OS.
    """
    if args is None:
        args = argparse.Namespace(pattern1=None, pattern2=None, verbose=False)

    if operating_system == _os.ANDROID:
        _dispatch_android(platform, args, no_argument)
    elif operating_system == _os.IOS:
        _dispatch_ios(platform, args, no_argument)
    else:
        raise PlatformNotSupported(operating_system)


def _dispatch_android(platform: str, args: "argparse.Namespace",
                      no_argument: bool) -> None:
    from platforms_android import firebase, univesal_analytics, appsflyer, gtm

    match platform:
        case _platforms.GA4_EVENTS:
            firebase.no_arguments() if no_argument else firebase.with_arguments(args)
        case _platforms.GA4_USER_PROPERTY:
            firebase.view_user_property()
        case _platforms.GAU:
            univesal_analytics.no_arguments() if no_argument else univesal_analytics.with_arguments(args)
        case _platforms.APPSFLYER:
            appsflyer.appsflyer_logs()
        case _platforms.GTM:
            gtm.main()
        case _:
            raise PlatformNotSupported(platform)


def _dispatch_ios(platform: str, args: "argparse.Namespace",
                  no_argument: bool) -> None:
    from platforms_ios import firebase_ios, universal_analytics_ios
    from platforms_ios import appsflyer as appsflyer_ios

    match platform:
        case _platforms.GA4_EVENTS:
            if no_argument or (args.pattern1 is None and args.pattern2 is None):
                firebase_ios.get_event_log(number_arguments=0)
            elif args.pattern1 is not None and args.pattern2 is not None:
                firebase_ios.get_event_log(number_arguments=2, pattern1=args.pattern1, pattern2=args.pattern2)
            else:
                term = args.pattern1 if args.pattern1 is not None else args.pattern2
                firebase_ios.get_event_log(number_arguments=1, pattern1=term)
        case _platforms.GAU:
            universal_analytics_ios.no_arguments() if no_argument else universal_analytics_ios.with_arguments(args)
        case _platforms.APPSFLYER:
            appsflyer_ios.appsflyer()
        case _:
            raise PlatformNotSupported(platform)
