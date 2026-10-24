import hashlib
import hmac
import os
import re

from app.utils.exceptions import ValidationError

ITERATIONS = 120000

PASSWORD_RULES = (
    "At least 8 characters with an uppercase letter, "
    "a lowercase letter, a digit and a symbol"
)


def validate_password(password):
    problems = []
    if len(password) < 8:
        problems.append("at least 8 characters")
    if not re.search(r"[A-Z]", password):
        problems.append("an uppercase letter")
    if not re.search(r"[a-z]", password):
        problems.append("a lowercase letter")
    if not re.search(r"\d", password):
        problems.append("a digit")
    if not re.search(r"[^A-Za-z0-9]", password):
        problems.append("a symbol")
    if re.search(r"\s", password):
        problems.append("no spaces")
    if problems:
        raise ValidationError("Weak password. It needs: " + ", ".join(problems) + ".")
    return password


def hash_password(password):
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return salt.hex() + "$" + digest.hex()


def verify_password(password, stored):
    try:
        salt_hex, digest_hex = stored.split("$")
        salt = bytes.fromhex(salt_hex)
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return hmac.compare_digest(digest.hex(), digest_hex)
