from app import config
from app.utils import clock
from app.utils.exceptions import NotFoundError, ValidationError


class OrderItem:
    def __init__(self, item_id, name, unit_price, quantity):
        self.__item_id = item_id
        self.__name = name
        self.__unit_price = unit_price
        self.quantity = quantity

    @classmethod
    def from_menu_item(cls, menu_item, quantity):
        return cls(menu_item.item_id, menu_item.name, menu_item.price, quantity)

    @property
    def item_id(self):
        return self.__item_id

    @property
    def name(self):
        return self.__name

    @property
    def unit_price(self):
        return self.__unit_price

    @property
    def quantity(self):
        return self.__quantity

    @quantity.setter
    def quantity(self, value):
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValidationError("Quantity must be a whole number greater than 0.")
        self.__quantity = value

    @property
    def subtotal(self):
        return round(self.__unit_price * self.__quantity, 2)

    def to_dict(self):
        return {
            "item_id": self.__item_id,
            "name": self.__name,
            "unit_price": self.__unit_price,
            "quantity": self.__quantity,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(int(data["item_id"]), data["name"], float(data["unit_price"]), data["quantity"])


class Order:
    OPEN = "Open"
    BILLED = "Billed"
    CANCELLED = "Cancelled"
    STATUSES = (OPEN, BILLED, CANCELLED)

    def __init__(self, order_id, customer, items=None, status=OPEN, created_at=None):
        if status not in Order.STATUSES:
            raise ValidationError(f"Invalid order status '{status}'.")
        self.__order_id = order_id
        self.__customer = customer
        self.__items = list(items or [])
        self.__status = status
        self.__created_at = created_at or clock.now()

    @property
    def order_id(self):
        return self.__order_id

    @property
    def customer(self):
        return self.__customer

    @property
    def items(self):
        return list(self.__items)

    @property
    def status(self):
        return self.__status

    @property
    def created_at(self):
        return self.__created_at

    def __check_editable(self):
        if self.__status != Order.OPEN:
            raise ValidationError(f"Order {self.__order_id} is {self.__status} and cannot be changed.")

    def find_item(self, item_id):
        for order_item in self.__items:
            if order_item.item_id == item_id:
                return order_item
        return None

    def add_item(self, menu_item, quantity):
        self.__check_editable()
        existing = self.find_item(menu_item.item_id)
        if existing:
            existing.quantity = existing.quantity + quantity
        else:
            self.__items.append(OrderItem.from_menu_item(menu_item, quantity))

    def update_quantity(self, item_id, quantity):
        self.__check_editable()
        order_item = self.find_item(item_id)
        if order_item is None:
            raise NotFoundError(f"Item {item_id} is not in this order.")
        order_item.quantity = quantity

    def remove_item(self, item_id):
        self.__check_editable()
        order_item = self.find_item(item_id)
        if order_item is None:
            raise NotFoundError(f"Item {item_id} is not in this order.")
        if len(self.__items) == 1:
            raise ValidationError("An order must keep at least one item. Cancel the order instead.")
        self.__items.remove(order_item)

    def cancel(self):
        self.__check_editable()
        self.__status = Order.CANCELLED

    def mark_billed(self):
        self.__check_editable()
        self.__status = Order.BILLED

    def subtotal(self):
        return round(sum(item.subtotal for item in self.__items), 2)

    def tax(self):
        return round(self.subtotal() * config.TAX_RATE, 2)

    def total(self):
        return round(self.subtotal() + self.tax(), 2)

    def to_dict(self):
        return {
            "order_id": self.__order_id,
            "customer_id": self.__customer.customer_id,
            "status": self.__status,
            "created_at": clock.format_datetime(self.__created_at),
            "items": [item.to_dict() for item in self.__items],
        }

    @classmethod
    def from_dict(cls, data, customer):
        try:
            items = [OrderItem.from_dict(entry) for entry in data["items"]]
            if not items:
                raise ValueError
            return cls(
                int(data["order_id"]),
                customer,
                items,
                data["status"],
                clock.parse_datetime(data["created_at"]),
            )
        except (KeyError, TypeError, ValueError, AttributeError):
            raise ValidationError("An order record in the data file is invalid.")
