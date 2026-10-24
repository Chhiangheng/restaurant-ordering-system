import os
import shutil
import sys
from getpass import getpass

from app.utils.colors import paint, visible_len


def term_width():
    return max(shutil.get_terminal_size((100, 30)).columns, 40)


def clear_screen():
    if sys.stdout.isatty():
        os.system("cls" if os.name == "nt" else "clear")


def center_line(text):
    pad = max(0, (term_width() - visible_len(text)) // 2)
    return " " * pad + text


def say(text="", *styles):
    for line in str(text).splitlines() or [""]:
        print(center_line(paint(line, *styles)) if line.strip() else "")


def print_block(text):
    lines = str(text).splitlines()
    if not lines:
        return
    pad = " " * max(0, (term_width() - max(visible_len(line) for line in lines)) // 2)
    for line in lines:
        print(pad + line if line.strip() else "")


def split_prompt(prompt):
    prompt = str(prompt)
    blank_lines = len(prompt) - len(prompt.lstrip("\n"))
    for _ in range(blank_lines):
        print()
    text = prompt.lstrip("\n")
    pad = " " * max(0, (term_width() - len(text)) // 2)
    return pad, text


def ask(prompt):
    pad, text = split_prompt(prompt)
    return input(pad + paint(text, "cyan"))


def ask_secret(prompt):
    pad, text = split_prompt(prompt)
    return getpass(pad + paint(text, "cyan"))


def banner(title, *subtitles):
    width = term_width()
    print(paint("=" * width, "cyan"))
    print(center_line(paint(title, "bold", "white")))
    for subtitle in subtitles:
        if subtitle:
            print(center_line(paint(subtitle, "dim")))
    print(paint("=" * width, "cyan"))


def screen(title, *subtitles):
    clear_screen()
    banner(title, *subtitles)
    print()


def section(title):
    say()
    say(title, "bold", "cyan")
    say("-" * len(title), "cyan")
