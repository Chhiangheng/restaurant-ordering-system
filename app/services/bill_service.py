from app.models.bill import Bill
from app.utils.exceptions import AppError, NotFoundError


class BillService:
    def __init__(self, store, order_service):
        self.__store = store
        self.__order_service = order_service
        self.__bills = {}
        self.notices = []
        self.__load()

    def __load(self):
        for record in self.__store.load():
            try:
                order = self.__order_service.get_order(record["order_id"])
                if order is None:
                    raise NotFoundError(f"Bill {record.get('bill_id')} was ignored because its order is missing.")
                bill = Bill.from_dict(record, order)
            except (AppError, KeyError, TypeError) as error:
                self.notices.append(str(error) if isinstance(error, AppError) else "A bill record is invalid.")
                continue
            if bill.bill_id in self.__bills:
                self.notices.append(f"Duplicate bill ID {bill.bill_id} was ignored.")
                continue
            self.__bills[bill.bill_id] = bill
        self.notices.extend(self.__store.notices)

    def __save(self):
        self.__store.save([bill.to_dict() for bill in self.get_all_bills()])

    def __next_id(self):
        return max(self.__bills, default=0) + 1

    def generate_bill(self, order_id):
        order = self.__order_service.require_order(order_id)
        self.__order_service.mark_billed(order_id)
        bill = Bill(self.__next_id(), order)
        self.__bills[bill.bill_id] = bill
        self.__save()
        return bill

    def record_payment(self, bill_id, method, amount_paid=None):
        bill = self.require_bill(bill_id)
        bill.record_payment(method, amount_paid)
        self.__save()
        return bill

    def get_bill(self, bill_id):
        return self.__bills.get(bill_id)

    def require_bill(self, bill_id):
        bill = self.get_bill(bill_id)
        if bill is None:
            raise NotFoundError(f"Bill {bill_id} was not found.")
        return bill

    def get_all_bills(self):
        return [self.__bills[key] for key in sorted(self.__bills)]

    def get_unpaid_bills(self):
        return [bill for bill in self.get_all_bills() if not bill.is_paid]

    def search_bills(self, keyword):
        keyword = keyword.strip().lower()
        return [
            bill for bill in self.get_all_bills()
            if keyword == str(bill.bill_id)
            or keyword == str(bill.order.order_id)
            or keyword in bill.customer.name.lower()
            or keyword == bill.status.lower()
            or keyword == (bill.payment_method or "").lower()
        ]
