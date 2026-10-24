from app.models.order import Order
from app.utils.exceptions import AppError, NotFoundError, ValidationError


class OrderService:
    def __init__(self, store, menu_service, customer_service):
        self.__store = store
        self.__menu_service = menu_service
        self.__customer_service = customer_service
        self.__orders = {}
        self.notices = []
        self.__load()

    def __load(self):
        for record in self.__store.load():
            try:
                customer = self.__customer_service.get_customer(record["customer_id"])
                if customer is None:
                    raise NotFoundError(f"Order {record.get('order_id')} was ignored because its customer is missing.")
                order = Order.from_dict(record, customer)
            except (AppError, KeyError, TypeError) as error:
                self.notices.append(str(error) if isinstance(error, AppError) else "An order record is invalid.")
                continue
            if order.order_id in self.__orders:
                self.notices.append(f"Duplicate order ID {order.order_id} was ignored.")
                continue
            self.__orders[order.order_id] = order
        self.notices.extend(self.__store.notices)

    def __save(self):
        self.__store.save([order.to_dict() for order in self.get_all_orders()])

    def __next_id(self):
        return max(self.__orders, default=0) + 1

    def __build_order(self, customer_id, selections):
        customer = self.__customer_service.require_customer(customer_id)
        if not selections:
            raise ValidationError("An order needs at least one item.")
        order = Order(self.__next_id(), customer)
        for item_id, quantity in selections:
            order.add_item(self.__menu_service.require_item(item_id), quantity)
        return order

    def preview_order(self, customer_id, selections):
        return self.__build_order(customer_id, selections)

    def create_order(self, customer_id, selections):
        order = self.__build_order(customer_id, selections)
        self.__orders[order.order_id] = order
        self.__save()
        return order

    def get_order(self, order_id):
        return self.__orders.get(order_id)

    def require_order(self, order_id):
        order = self.get_order(order_id)
        if order is None:
            raise NotFoundError(f"Order {order_id} was not found.")
        return order

    def get_all_orders(self):
        return [self.__orders[key] for key in sorted(self.__orders)]

    def add_item(self, order_id, item_id, quantity):
        order = self.require_order(order_id)
        order.add_item(self.__menu_service.require_item(item_id), quantity)
        self.__save()

    def update_item_quantity(self, order_id, item_id, quantity):
        self.require_order(order_id).update_quantity(item_id, quantity)
        self.__save()

    def remove_item(self, order_id, item_id):
        self.require_order(order_id).remove_item(item_id)
        self.__save()

    def cancel_order(self, order_id):
        self.require_order(order_id).cancel()
        self.__save()

    def mark_billed(self, order_id):
        order = self.require_order(order_id)
        if order.status == Order.CANCELLED:
            raise ValidationError("A cancelled order cannot be billed.")
        if order.status == Order.BILLED:
            raise ValidationError("This order already has a bill.")
        order.mark_billed()
        self.__save()

    def get_orders_for_customer(self, customer_id):
        return [o for o in self.get_all_orders() if o.customer.customer_id == customer_id]

    def count_for_customer(self, customer_id):
        return len(self.get_orders_for_customer(customer_id))

    def search_orders(self, keyword):
        keyword = keyword.strip().lower()
        results = []
        for order in self.get_all_orders():
            names = " ".join(item.name.lower() for item in order.items)
            if (keyword == str(order.order_id)
                    or keyword in order.customer.name.lower()
                    or keyword == str(order.customer.customer_id).lower()
                    or keyword == order.status.lower()
                    or keyword in names):
                results.append(order)
        return results
