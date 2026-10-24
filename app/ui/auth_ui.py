from app import config
from app.ui.common import open_screen
from app.utils import feedback
from app.utils.exceptions import AppError, AuthenticationError
from app.utils.layout import say, screen
from app.utils.validators import read_new_password, read_password, read_text


def login(app):
    screen("LOGIN", config.APP_TITLE)
    say("Enter your username and password\n", "dim")
    for attempt in range(1, config.MAX_LOGIN_ATTEMPTS + 1):
        username = read_text("Username: ")
        password = read_password("Password: ")
        try:
            user = app.auth_service.login(username, password)
        except AuthenticationError as error:
            remaining = config.MAX_LOGIN_ATTEMPTS - attempt
            feedback.error(str(error))
            if remaining:
                feedback.warning(f"{remaining} attempt(s) left.")
                print()
            continue
        print()
        feedback.progress("Signing in")
        feedback.success(f"Welcome, {user.full_name}! Role: {user.role}.")
        return True
    feedback.error("Too many failed attempts. Returning to the start screen.")
    return False


def change_password(app):
    open_screen(app, "CHANGE PASSWORD")
    current = read_password("Current password: ")
    print()
    new_password = read_new_password()
    try:
        app.auth_service.change_own_password(current, new_password)
    except AppError as error:
        feedback.error(str(error))
        return
    feedback.success("Your password was changed.")
