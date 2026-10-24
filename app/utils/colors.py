import os
import re
import sys

try:
    import colorama
    colorama.just_fix_windows_console()
except Exception:
    pass

ANSI_PATTERN = re.compile(r"\033\[[0-9;]*m")

CODES = {
    "reset": "0",
    "bold": "1",
    "dim": "2",
    "red": "31",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "magenta": "35",
    "cyan": "36",
    "white": "37",
}


def color_enabled():
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return sys.stdout.isatty()


def paint(text, *styles):
    if not styles or not color_enabled():
        return str(text)
    start = "".join(f"\033[{CODES[style]}m" for style in styles)
    return f"{start}{text}\033[0m"


def strip_ansi(text):
    return ANSI_PATTERN.sub("", str(text))


def visible_len(text):
    return len(strip_ansi(text))
