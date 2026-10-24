import re

from app.models.menu import CATEGORIES
from app.utils import feedback, rules, security
from app.utils.exceptions import ValidationError
from app.utils.layout import ask, ask_secret, say


def read_text(prompt, allow_blank=False):
    while True:
        value = ask(prompt).strip()
        if value or allow_blank:
            return value
        feedback.error("Input cannot be empty.")


def read_int(prompt, minimum=None, maximum=None, allow_blank=False):
    while True:
        text = ask(prompt).strip()
        if text == "" and allow_blank:
            return None
        if not re.fullmatch(r"\d+", text):
            feedback.error("Please enter a whole number.")
            continue
        value = int(text)
        if minimum is not None and value < minimum:
            feedback.error(f"Number must be at least {minimum}.")
        elif maximum is not None and value > maximum:
            feedback.error(f"Number must be at most {maximum}.")
        else:
            return value


def read_choice(prompt, count):
    while True:
        text = ask(prompt).strip()
        if re.fullmatch(r"\d+", text) and 1 <= int(text) <= count:
            return int(text)
        feedback.error(f"Invalid menu selection. Choose a number from 1 to {count}.")


def read_validated(prompt, checker, allow_blank=False):
    while True:
        value = ask(prompt).strip()
        if value == "" and allow_blank:
            return None
        try:
            return checker(value)
        except ValidationError as error:
            feedback.error(str(error))


def read_price(prompt, allow_blank=False):
    return read_validated(prompt, rules.check_price, allow_blank)


def read_name(prompt, allow_blank=False):
    return read_validated(prompt, rules.check_name, allow_blank)


def read_phone(prompt, allow_blank=False):
    return read_validated(prompt, rules.check_phone, allow_blank)


def read_username(prompt):
    return read_validated(prompt, rules.check_username)


def read_date(prompt, default=None):
    value = read_validated(prompt, rules.check_date, allow_blank=default is not None)
    return default if value is None else value


def read_month(prompt, default=None):
    value = read_validated(prompt, rules.check_month, allow_blank=default is not None)
    return default if value is None else value


def read_category(allow_blank=False):
    options = "/".join(f"{index}={name}" for index, name in enumerate(CATEGORIES, 1))
    hint = ", Enter to keep" if allow_blank else ""
    choice = read_int(f"Category ({options}{hint}): ", 1, len(CATEGORIES), allow_blank)
    return None if choice is None else CATEGORIES[choice - 1]


def confirm(prompt):
    while True:
        answer = ask(prompt + " (y/n): ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        feedback.error("Please type y or n.")


def read_password(prompt="Password: "):
    return ask_secret(prompt)


def read_new_password(prompt="New password: "):
    say(security.PASSWORD_RULES, "dim")
    while True:
        password = ask_secret(prompt)
        try:
            security.validate_password(password)
        except ValidationError as error:
            feedback.error(str(error))
            continue
        if ask_secret("Confirm password: ") != password:
            feedback.error("Passwords do not match. Try again.")
            continue
        return password
