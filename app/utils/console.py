from app.utils.layout import ask, print_block, screen
from app.utils.validators import read_choice


def pause():
    ask("\nPress Enter to continue...")


def show_menu(title, options, subtitles=(), descriptions=None, show_header=True):
    if show_header:
        screen(title, *subtitles)
    entries = []
    for number, text in enumerate(options, 1):
        lines = [f"{number}. {text}"]
        if descriptions and descriptions[number - 1]:
            lines.append(f"   {descriptions[number - 1]}")
        entries.append("\n".join(lines))
    separator = "\n\n" if descriptions else "\n"
    print_block(separator.join(entries))
    print()
    return read_choice("Enter your choice: ", len(options))
