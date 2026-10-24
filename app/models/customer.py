from app.utils import rules
from app.utils.exceptions import ValidationError


class Customer:
    def __init__(self, customer_id, name, phone):
        self.__customer_id = customer_id
        self.name = name
        self.phone = phone

    @property
    def customer_id(self):
        return self.__customer_id

    @property
    def is_walk_in(self):
        return isinstance(self.__customer_id, str)

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, value):
        self.__name = rules.check_text(value, "Customer name")

    @property
    def phone(self):
        return self.__phone

    @phone.setter
    def phone(self, value):
        self.__phone = rules.check_text(value, "Phone number")

    @property
    def label(self):
        if self.is_walk_in:
            return self.__name
        return f"{self.__name} (ID {self.__customer_id})"

    def to_dict(self):
        return {"customer_id": self.__customer_id, "name": self.__name, "phone": self.__phone}

    @classmethod
    def from_dict(cls, data):
        try:
            customer_id = data["customer_id"]
            if not isinstance(customer_id, (int, str)) or isinstance(customer_id, bool):
                raise ValueError
            return cls(customer_id, data["name"], data["phone"])
        except (KeyError, TypeError, ValueError, AttributeError):
            raise ValidationError("A customer record in the data file is invalid.")
