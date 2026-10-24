from app.utils import rules
from app.utils.exceptions import DuplicateError, NotFoundError, ValidationError

CATEGORIES = ("Food", "Drink")


class MenuItem:
    def __init__(self, item_id, name, price, category):
        self.__item_id = item_id
        self.name = name
        self.price = price
        self.category = category

    @property
    def item_id(self):
        return self.__item_id

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, value):
        self.__name = rules.check_text(value, "Item name")

    @property
    def price(self):
        return self.__price

    @price.setter
    def price(self, value):
        self.__price = rules.check_price(value)

    @property
    def category(self):
        return self.__category

    @category.setter
    def category(self, value):
        value = str(value).strip().title()
        if value not in CATEGORIES:
            raise ValidationError("Category must be one of: " + ", ".join(CATEGORIES))
        self.__category = value

    def to_dict(self):
        return {
            "item_id": self.__item_id,
            "name": self.__name,
            "price": self.__price,
            "category": self.__category,
        }

    @classmethod
    def from_dict(cls, data):
        try:
            return cls(int(data["item_id"]), data["name"], data["price"], data["category"])
        except (KeyError, TypeError, ValueError, AttributeError):
            raise ValidationError("A menu record in the data file is invalid.")


class Menu:
    def __init__(self):
        self.__items = {}

    def restore(self, item):
        if item.item_id in self.__items:
            raise DuplicateError(f"Duplicate menu item ID {item.item_id} was ignored.")
        self.__items[item.item_id] = item

    def __next_id(self):
        return max(self.__items, default=0) + 1

    def __ensure_unique_name(self, name, ignore_id=None):
        for item in self.__items.values():
            if item.item_id != ignore_id and item.name.lower() == str(name).strip().lower():
                raise DuplicateError(f"A menu item named '{item.name}' already exists.")

    def add_item(self, name, price, category):
        self.__ensure_unique_name(name)
        item = MenuItem(self.__next_id(), name, price, category)
        self.__items[item.item_id] = item
        return item

    def get_item(self, item_id):
        return self.__items.get(item_id)

    def require_item(self, item_id):
        item = self.get_item(item_id)
        if item is None:
            raise NotFoundError(f"Menu item {item_id} was not found.")
        return item

    def get_all_items(self):
        return [self.__items[key] for key in sorted(self.__items)]

    def update_item(self, item_id, name=None, price=None, category=None):
        item = self.require_item(item_id)
        if name is not None:
            self.__ensure_unique_name(name, item_id)
            item.name = name
        if price is not None:
            item.price = price
        if category is not None:
            item.category = category
        return item

    def delete_item(self, item_id):
        self.require_item(item_id)
        return self.__items.pop(item_id)

    def search(self, keyword):
        keyword = keyword.strip().lower()
        return [
            item for item in self.get_all_items()
            if keyword == str(item.item_id)
            or keyword in item.name.lower()
            or keyword in item.category.lower()
        ]
