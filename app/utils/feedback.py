import os
import sys
import time

from app.utils.colors import paint
from app.utils.layout import center_line, say


def success(message):
    say(f"✔ {message}", "green", "bold")


def error(message):
    say(f"✖ {message}", "red", "bold")


def warning(message):
    say(f"! {message}", "yellow")


def info(message):
    say(f"i {message}", "cyan")


def progress(label, steps=24, delay=0.012):
    fast = bool(os.environ.get("RESTAURANT_FAST")) or not sys.stdout.isatty()
    last = ""
    for index in range(steps + 1):
        bar = "█" * index + "░" * (steps - index)
        last = center_line(paint(f"{label} [{bar}] {index * 100 // steps:3d}%", "cyan"))
        if not fast:
            sys.stdout.write("\r" + last)
            sys.stdout.flush()
            time.sleep(delay)
    if fast:
        print(last)
    else:
        print()
