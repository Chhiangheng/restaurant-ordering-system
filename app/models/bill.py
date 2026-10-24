from app import config
from app.utils import clock
from app.utils.exceptions import ValidationError


class Bill:
    PAYMENT_METHODS = ("Cash", "Card", "KHQR")

    def __init__(self, bill_id, order, lines=None, issued_at=None, tax_rate=None, payment=None):
        self.__bill_id = bill_id
        self.__order = order
        self.__customer = order.customer
        self.__issued_at = issued_at or clock.now()
        self.__tax_rate = config.TAX_RATE if tax_rate is None else tax_rate
        if lines is None:
            lines = [
                {
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "subtotal": item.subtotal,
                }
                for item in order.items
            ]
        self.__lines = lines
        self.__subtotal = round(sum(line["subtotal"] for line in lines), 2)
        self.__tax = round(self.__subtotal * self.__tax_rate, 2)
        self.__total = round(self.__subtotal + self.__tax, 2)
        payment = payment or {}
        self.__payment_method = payment.get("method")
        self.__amount_paid = payment.get("amount_paid", 0.0)
        self.__change = payment.get("change", 0.0)
        self.__paid_at = payment.get("paid_at")

    @property
    def bill_id(self):
        return self.__bill_id

    @property
    def order(self):
        return self.__order

    @property
    def customer(self):
        return self.__customer

    @property
    def issued_at(self):
        return self.__issued_at

    @property
    def tax_rate(self):
        return self.__tax_rate

    @property
    def lines(self):
        return [dict(line) for line in self.__lines]

    @property
    def subtotal(self):
        return self.__subtotal

    @property
    def tax(self):
        return self.__tax

    @property
    def total(self):
        return self.__total

    @property
    def is_paid(self):
        return self.__paid_at is not None

    @property
    def status(self):
        return "Paid" if self.is_paid else "Unpaid"

    @property
    def payment_method(self):
        return self.__payment_method

    @property
    def amount_paid(self):
        return self.__amount_paid

    @property
    def change(self):
        return self.__change

    @property
    def paid_at(self):
        return self.__paid_at

    def record_payment(self, method, amount_paid=None):
        if self.is_paid:
            raise ValidationError("This bill is already paid.")
        matches = [m for m in self.PAYMENT_METHODS if m.lower() == str(method).strip().lower()]
        if not matches:
            raise ValidationError("Payment method must be: " + ", ".join(self.PAYMENT_METHODS))
        method = matches[0]
        if method != "Cash" or amount_paid is None:
            amount_paid = self.__total
        amount_paid = round(float(amount_paid), 2)
        if amount_paid < self.__total:
            raise ValidationError(
                f"Amount received ({amount_paid:.2f}) is less than the total ({self.__total:.2f})."
            )
        self.__payment_method = method
        self.__amount_paid = amount_paid
        self.__change = round(amount_paid - self.__total, 2)
        self.__paid_at = clock.now()

    def to_dict(self):
        payment = None
        if self.is_paid:
            payment = {
                "method": self.__payment_method,
                "amount_paid": self.__amount_paid,
                "change": self.__change,
                "paid_at": clock.format_datetime(self.__paid_at),
            }
        return {
            "bill_id": self.__bill_id,
            "order_id": self.__order.order_id,
            "customer_id": self.__customer.customer_id,
            "issued_at": clock.format_datetime(self.__issued_at),
            "tax_rate": self.__tax_rate,
            "lines": self.__lines,
            "subtotal": self.__subtotal,
            "tax": self.__tax,
            "total": self.__total,
            "payment": payment,
        }

    @classmethod
    def from_dict(cls, data, order):
        try:
            payment = data.get("payment")
            if payment:
                payment = dict(payment)
                payment["paid_at"] = clock.parse_datetime(payment["paid_at"])
                payment["amount_paid"] = float(payment["amount_paid"])
                payment["change"] = float(payment["change"])
            lines = [
                {
                    "name": line["name"],
                    "quantity": int(line["quantity"]),
                    "unit_price": float(line["unit_price"]),
                    "subtotal": float(line["subtotal"]),
                }
                for line in data["lines"]
            ]
            return cls(
                int(data["bill_id"]),
                order,
                lines,
                clock.parse_datetime(data["issued_at"]),
                float(data["tax_rate"]),
                payment,
            )
        except (KeyError, TypeError, ValueError, AttributeError):
            raise ValidationError("A bill record in the data file is invalid.")
