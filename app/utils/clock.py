from datetime import datetime

from app import config


def now():
    return datetime.now()


def format_datetime(value):
    return value.strftime(config.DATETIME_FORMAT)


def parse_datetime(text):
    return datetime.strptime(text, config.DATETIME_FORMAT)
