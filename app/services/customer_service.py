import re

from app.models.customer import Customer
from app.utils import rules
from app.utils.exceptions import AppError, DuplicateError, NotFoundError, ValidationError


class CustomerService:
    def __init__(self, store):
        self.__store = store
        self.__customers = {}
        self.__walk_ins = {}
        self.__current = None
        self.__order_counter = lambda customer_id: 0
        self.notices = []
        self.__load()

    def __load(self):
        for record in self.__store.load():
            try:
                customer = Customer.from_dict(record)
            except AppError as error:
                self.notices.append(str(error))
                continue
            target = self.__walk_ins if customer.is_walk_in else self.__customers
            if customer.customer_id in target:
                self.notices.append(f"Duplicate customer ID {customer.customer_id} was ignored.")
                continue
            target[customer.customer_id] = customer
        self.notices.extend(self.__store.notices)

    def __save(self):
        records = [c.to_dict() for c in self.get_all_customers() + self.get_walk_in_customers()]
        self.__store.save(records)

    def set_order_counter(self, counter):
        self.__order_counter = counter

    def __next_registered_id(self):
        return max(self.__customers, default=0) + 1

    def __next_walk_in_id(self):
        numbers = [int(re.sub(r"\D", "", key) or 0) for key in self.__walk_ins]
        return f"W{max(numbers, default=0) + 1:03d}"

    def __ensure_unique_phone(self, phone, ignore_id=None):
        digits = re.sub(r"\D", "", phone)
        for customer in self.__customers.values():
            if customer.customer_id != ignore_id and re.sub(r"\D", "", customer.phone) == digits:
                raise DuplicateError(f"Phone number already belongs to {customer.name} (ID {customer.customer_id}).")

    def register_customer(self, name, phone):
        name = rules.check_name(name)
        phone = rules.check_phone(phone)
        self.__ensure_unique_phone(phone)
        customer = Customer(self.__next_registered_id(), name, phone)
        self.__customers[customer.customer_id] = customer
        self.__save()
        return customer

    def create_walk_in(self):
        walk_in_id = self.__next_walk_in_id()
        customer = Customer(walk_in_id, f"Walk-in {walk_in_id}", "-")
        self.__walk_ins[walk_in_id] = customer
        self.__save()
        return customer

    def update_customer(self, customer_id, name=None, phone=None):
        customer = self.require_customer(customer_id)
        if customer.is_walk_in:
            raise ValidationError("Walk-in customers cannot be edited.")
        if name is not None:
            customer.name = rules.check_name(name)
        if phone is not None:
            phone = rules.check_phone(phone)
            self.__ensure_unique_phone(phone, customer_id)
            customer.phone = phone
        self.__save()
        return customer

    def delete_customer(self, customer_id):
        customer = self.require_customer(customer_id)
        if customer.is_walk_in:
            raise ValidationError("Walk-in customers cannot be deleted.")
        if self.__order_counter(customer_id) > 0:
            raise ValidationError("This customer has orders and cannot be deleted.")
        del self.__customers[customer_id]
        if self.__current is customer:
            self.__current = None
        self.__save()
        return customer

    def get_customer(self, customer_id):
        if isinstance(customer_id, str):
            return self.__walk_ins.get(customer_id.upper())
        return self.__customers.get(customer_id)

    def require_customer(self, customer_id):
        customer = self.get_customer(customer_id)
        if customer is None:
            raise NotFoundError(f"Customer {customer_id} was not found.")
        return customer

    def find_by_text(self, text):
        text = str(text).strip()
        return self.get_customer(int(text)) if text.isdigit() else self.get_customer(text)

    def get_all_customers(self):
        return [self.__customers[key] for key in sorted(self.__customers)]

    def get_walk_in_customers(self):
        return [self.__walk_ins[key] for key in sorted(self.__walk_ins)]

    def search_customers(self, keyword):
        keyword = keyword.strip().lower()
        keyword_digits = re.sub(r"\D", "", keyword)
        everyone = self.get_all_customers() + self.get_walk_in_customers()
        results = []
        for customer in everyone:
            phone_digits = re.sub(r"\D", "", customer.phone)
            by_id = keyword == str(customer.customer_id).lower()
            by_name = keyword in customer.name.lower()
            by_phone = bool(keyword_digits) and keyword_digits in phone_digits
            if by_id or by_name or by_phone:
                results.append(customer)
        return results

    @property
    def current_customer(self):
        return self.__current

    def select_customer(self, customer_id):
        self.__current = self.require_customer(customer_id)
        return self.__current

    def select_new_walk_in(self):
        self.__current = self.create_walk_in()
        return self.__current

    def clear_selection(self):
        self.__current = None
