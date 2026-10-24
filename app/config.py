import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("RESTAURANT_DATA_DIR", BASE_DIR / "data"))

APP_TITLE = "RESTAURANT ORDERING SYSTEM"
STUDENT_NAME = "Pou Chhiangheng"

TAX_RATE = 0.10
CURRENCY = "$"
MAX_LOGIN_ATTEMPTS = 3

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

USERS_FILE = "users.json"
MENU_FILE = "menu.json"
CUSTOMERS_FILE = "customers.json"
ORDERS_FILE = "orders.json"
BILLS_FILE = "bills.json"
