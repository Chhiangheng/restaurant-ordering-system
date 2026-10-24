import re
from datetime import datetime

from app import config
from app.utils.exceptions import ValidationError

PHONE_PATTERN = re.compile(r"^\+?[\d\s-]+$")
USERNAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]{2,19}$")


def check_text(value, label="Value"):
    text = str(value).strip()
    if not text:
        raise ValidationError(f"{label} cannot be empty.")
    return text


def check_name(value):
    text = str(value).strip()
    valid = text and any(c.isalpha() for c in text) and all(c.isalpha() or c in " .-'" for c in text)
    if not valid:
        raise ValidationError("Name must contain letters only (spaces, . - ' allowed).")
    return text


def check_phone(value):
    text = str(value).strip()
    digits = re.sub(r"\D", "", text)
    if not PHONE_PATTERN.match(text) or not 8 <= len(digits) <= 15:
        raise ValidationError("Phone must have 8-15 digits (spaces, + and - allowed).")
    return text


def check_price(value):
    try:
        number = float(str(value).replace("$", "").strip())
    except ValueError:
        raise ValidationError("Price must be a number, for example 2.50.")
    if number <= 0:
        raise ValidationError("Price must be greater than 0.")
    return round(number, 2)


def check_username(value):
    text = str(value).strip()
    if not USERNAME_PATTERN.match(text):
        raise ValidationError(
            "Username must be 3-20 characters, start with a letter and use only letters, digits or underscore."
        )
    return text


def check_date(value):
    try:
        return datetime.strptime(str(value).strip(), config.DATE_FORMAT).date()
    except ValueError:
        raise ValidationError("Date must look like 2026-10-24.")


def check_month(value):
    try:
        parsed = datetime.strptime(str(value).strip(), "%Y-%m")
    except ValueError:
        raise ValidationError("Month must look like 2026-10.")
    return parsed.year, parsed.month
