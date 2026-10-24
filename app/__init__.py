from pathlib import Path

from app import config
from app.services.auth_service import AuthService
from app.services.bill_service import BillService
from app.services.customer_service import CustomerService
from app.services.menu_service import MenuService
from app.services.order_service import OrderService
from app.services.report_service import ReportService
from app.storage import defaults
from app.storage.json_store import JsonStore


class RestaurantApp:
    def __init__(self, data_dir=None):
        directory = Path(data_dir) if data_dir else config.DATA_DIR
        self.data_dir = directory
        self.auth_service = AuthService(JsonStore(directory / config.USERS_FILE, defaults.default_users))
        self.menu_service = MenuService(
            JsonStore(directory / config.MENU_FILE, defaults.default_menu), self.auth_service
        )
        self.customer_service = CustomerService(
            JsonStore(directory / config.CUSTOMERS_FILE, defaults.default_customers)
        )
        self.order_service = OrderService(
            JsonStore(directory / config.ORDERS_FILE, defaults.empty_list),
            self.menu_service,
            self.customer_service,
        )
        self.customer_service.set_order_counter(self.order_service.count_for_customer)
        self.bill_service = BillService(
            JsonStore(directory / config.BILLS_FILE, defaults.empty_list), self.order_service
        )
        self.report_service = ReportService(
            self.auth_service,
            self.menu_service,
            self.customer_service,
            self.order_service,
            self.bill_service,
        )
        self.notices = (
            self.auth_service.notices
            + self.menu_service.notices
            + self.customer_service.notices
            + self.order_service.notices
            + self.bill_service.notices
        )

    def run(self):
        from app.ui import main_menu
        main_menu.run(self)
