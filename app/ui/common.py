from app.utils import feedback
from app.utils.console import pause, show_menu
from app.utils.exceptions import AppError
from app.utils.layout import print_block, say, screen


def user_line(app):
    user = app.auth_service.current_user
    if user is None:
        return ""
    return f"Logged in as {user.full_name} ({user.role})"


def open_screen(app, title, *extra):
    screen(title, user_line(app), *extra)


def show_table(text, count=None, label="record"):
    print_block(text)
    if count is not None:
        say(f"\n{count} {label}(s)", "dim")


def run_menu(app, title, actions, extra=None):
    labels = [label for label, _ in actions] + ["Back to Main Menu"]
    while True:
        subtitles = [user_line(app)] + (extra(app) if extra else [])
        choice = show_menu(title, labels, subtitles=subtitles)
        if choice == len(labels):
            return
        try:
            actions[choice - 1][1](app)
        except AppError as error:
            feedback.error(str(error))
        pause()
