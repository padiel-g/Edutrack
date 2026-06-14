import secrets
import string
import re


SPECIAL_CHARACTERS = "!@#$%&*"


def is_strong_password(password):
    return (
        isinstance(password, str)
        and len(password) >= 10
        and bool(re.search(r"[A-Z]", password))
        and bool(re.search(r"[a-z]", password))
        and bool(re.search(r"\d", password))
        and bool(re.search(r"[^A-Za-z0-9]", password))
    )


def generate_temporary_password(length=16):
    if length < 12:
        raise ValueError("Temporary passwords must contain at least 12 characters.")
    required = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice(SPECIAL_CHARACTERS),
    ]
    alphabet = string.ascii_letters + string.digits + SPECIAL_CHARACTERS
    characters = required + [secrets.choice(alphabet) for _ in range(length - len(required))]
    secrets.SystemRandom().shuffle(characters)
    return "".join(characters)
