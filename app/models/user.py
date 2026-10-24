from app.utils import rules
from app.utils.exceptions import ValidationError

ROLES = ("admin", "manager", "cashier")

PERMISSIONS = {
    "admin": {"menu.view", "menu.edit", "customers", "orders", "bills", "reports", "users"},
    "manager": {"menu.view", "menu.edit", "customers", "orders", "bills", "reports"},
    "cashier": {"menu.view", "customers", "orders", "bills"},
}


class User:
    def __init__(self, user_id, username, password_hash, role, full_name,
                 active=True, created_at="", last_login=""):
        self.__user_id = user_id
        self.__username = username
        self.__created_at = created_at
        self.password_hash = password_hash
        self.role = role
        self.full_name = full_name
        self.active = active
        self.last_login = last_login

    @property
    def user_id(self):
        return self.__user_id

    @property
    def username(self):
        return self.__username

    @property
    def created_at(self):
        return self.__created_at

    @property
    def password_hash(self):
        return self.__password_hash

    @password_hash.setter
    def password_hash(self, value):
        self.__password_hash = rules.check_text(value, "Password")

    @property
    def role(self):
        return self.__role

    @role.setter
    def role(self, value):
        value = str(value).strip().lower()
        if value not in ROLES:
            raise ValidationError("Role must be one of: " + ", ".join(ROLES))
        self.__role = value

    @property
    def full_name(self):
        return self.__full_name

    @full_name.setter
    def full_name(self, value):
        self.__full_name = rules.check_text(value, "Full name")

    @property
    def active(self):
        return self.__active

    @active.setter
    def active(self, value):
        self.__active = bool(value)

    @property
    def last_login(self):
        return self.__last_login

    @last_login.setter
    def last_login(self, value):
        self.__last_login = str(value or "")

    def can(self, permission):
        return permission in PERMISSIONS[self.__role]

    def to_dict(self):
        return {
            "user_id": self.__user_id,
            "username": self.__username,
            "password_hash": self.__password_hash,
            "role": self.__role,
            "full_name": self.__full_name,
            "active": self.__active,
            "created_at": self.__created_at,
            "last_login": self.__last_login,
        }

    @classmethod
    def from_dict(cls, data):
        try:
            return cls(
                int(data["user_id"]),
                data["username"],
                data["password_hash"],
                data["role"],
                data["full_name"],
                data.get("active", True),
                data.get("created_at", ""),
                data.get("last_login", ""),
            )
        except (KeyError, TypeError, ValueError, AttributeError):
            raise ValidationError("A user record in the data file is invalid.")
