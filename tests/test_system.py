import io
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path
from unittest.mock import patch

from app import RestaurantApp
from app.utils import layout, security
from app.utils.exceptions import (
    AuthenticationError,
    DuplicateError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.directory = Path(tempfile.mkdtemp())
        self.app = RestaurantApp(self.directory)
        self.app.auth_service.login("admin", "Admin@123")

    def tearDown(self):
        shutil.rmtree(self.directory, ignore_errors=True)

    def reload(self):
        app = RestaurantApp(self.directory)
        app.auth_service.login("admin", "Admin@123")
        return app


class AuthTests(BaseTest):
    def test_login_logout(self):
        self.app.auth_service.logout()
        self.assertIsNone(self.app.auth_service.current_user)
        user = self.app.auth_service.login("Manager", "Manager@123")
        self.assertEqual(user.role, "manager")

    def test_incorrect_login(self):
        self.app.auth_service.logout()
        with self.assertRaises(AuthenticationError):
            self.app.auth_service.login("admin", "wrong")
        with self.assertRaises(AuthenticationError):
            self.app.auth_service.login("nobody", "Admin@123")

    def test_password_validation(self):
        for weak in ("short1!", "alllowercase1!", "ALLUPPERCASE1!", "NoDigits!!", "NoSymbol123"):
            with self.assertRaises(ValidationError):
                security.validate_password(weak)
        self.assertEqual(security.validate_password("Good@1234"), "Good@1234")

    def test_passwords_are_hashed(self):
        text = (self.directory / "users.json").read_text(encoding="utf-8")
        self.assertNotIn("Admin@123", text)

    def test_roles_and_permissions(self):
        self.app.auth_service.logout()
        self.app.auth_service.login("cashier", "Cashier@123")
        with self.assertRaises(PermissionDeniedError):
            self.app.menu_service.add_item("Tea", 1.0, "Drink")
        with self.assertRaises(PermissionDeniedError):
            self.app.report_service.total_records()
        with self.assertRaises(PermissionDeniedError):
            self.app.auth_service.get_all_users()

    def test_user_crud_and_duplicates(self):
        auth = self.app.auth_service
        user = auth.add_user("newuser", "Strong@123", "cashier", "New User")
        with self.assertRaises(DuplicateError):
            auth.add_user("NEWUSER", "Strong@123", "cashier", "Other")
        auth.update_user(user.user_id, full_name="Renamed", role="manager")
        self.assertEqual(auth.require_user(user.user_id).role, "manager")
        self.assertEqual(len(auth.search_users("renamed")), 1)
        auth.delete_user(user.user_id)
        with self.assertRaises(NotFoundError):
            auth.require_user(user.user_id)

    def test_last_admin_is_protected(self):
        auth = self.app.auth_service
        with self.assertRaises(ValidationError):
            auth.delete_user(1)
        with self.assertRaises(ValidationError):
            auth.update_user(1, active=False)

    def test_change_own_password(self):
        auth = self.app.auth_service
        with self.assertRaises(AuthenticationError):
            auth.change_own_password("bad", "Another@123")
        auth.change_own_password("Admin@123", "Another@123")
        auth.logout()
        auth.login("admin", "Another@123")


class MenuTests(BaseTest):
    def test_crud_and_persistence(self):
        menu = self.app.menu_service
        item = menu.add_item("Tea Latte", 2.8, "drink")
        self.assertEqual(item.category, "Drink")
        menu.update_item(item.item_id, price=3.0)
        self.assertEqual(self.reload().menu_service.get_item(item.item_id).price, 3.0)
        menu.delete_item(item.item_id)
        self.assertIsNone(self.reload().menu_service.get_item(item.item_id))

    def test_validation_and_duplicates(self):
        menu = self.app.menu_service
        with self.assertRaises(ValidationError):
            menu.add_item("Bad", -1, "Food")
        with self.assertRaises(ValidationError):
            menu.add_item("Bad", 1, "Toys")
        with self.assertRaises(DuplicateError):
            menu.add_item("fried rice", 3, "Food")

    def test_search(self):
        menu = self.app.menu_service
        self.assertEqual(len(menu.search_items("drink")), 5)
        self.assertEqual(menu.search_items("amok")[0].name, "Fish Amok")


class CustomerTests(BaseTest):
    def test_register_search_update_delete(self):
        customers = self.app.customer_service
        new = customers.register_customer("Test User", "011223344")
        self.assertEqual(customers.search_customers("test")[0], new)
        self.assertEqual(customers.search_customers("011223344")[0], new)
        with self.assertRaises(DuplicateError):
            customers.register_customer("Other Person", "011 223 344")
        customers.update_customer(new.customer_id, name="Test Renamed")
        self.assertEqual(self.reload().customer_service.get_customer(new.customer_id).name, "Test Renamed")
        customers.delete_customer(new.customer_id)
        with self.assertRaises(NotFoundError):
            customers.require_customer(new.customer_id)

    def test_customer_with_orders_cannot_be_deleted(self):
        self.app.order_service.create_order(1, [(1, 1)])
        with self.assertRaises(ValidationError):
            self.app.customer_service.delete_customer(1)

    def test_walk_in_ids_are_generated_and_saved(self):
        customers = self.app.customer_service
        first = customers.create_walk_in()
        second = customers.create_walk_in()
        self.assertEqual((first.customer_id, second.customer_id), ("W001", "W002"))
        self.assertEqual(self.reload().customer_service.get_customer("w002").customer_id, "W002")
        self.assertNotIn(first, customers.get_all_customers())

    def test_current_customer_is_reused(self):
        customers = self.app.customer_service
        customers.select_customer(1)
        orders = self.app.order_service
        orders.create_order(customers.current_customer.customer_id, [(1, 1)])
        orders.create_order(customers.current_customer.customer_id, [(2, 1)])
        self.assertEqual(len(orders.get_orders_for_customer(1)), 2)
        with self.assertRaises(NotFoundError):
            customers.select_customer(99)


class OrderBillTests(BaseTest):
    def test_totals_and_persistence(self):
        order = self.app.order_service.create_order(1, [(1, 2), (6, 1)])
        self.assertEqual((order.subtotal(), order.tax(), order.total()), (9.00, 0.90, 9.90))
        saved = self.reload().order_service.get_order(order.order_id)
        self.assertEqual(saved.total(), 9.90)

    def test_preview_is_not_saved(self):
        walk_in = self.app.customer_service.create_walk_in()
        preview = self.app.order_service.preview_order(walk_in.customer_id, [(1, 1)])
        self.assertEqual(self.app.order_service.get_all_orders(), [])
        order = self.app.order_service.create_order(walk_in.customer_id, [(1, 1)])
        self.assertEqual(preview.order_id, order.order_id)

    def test_update_and_cancel(self):
        orders = self.app.order_service
        order = orders.create_order(1, [(1, 1)])
        orders.add_item(order.order_id, 6, 2)
        orders.update_item_quantity(order.order_id, 1, 3)
        self.assertEqual(order.subtotal(), 3 * 3.50 + 2 * 2.00)
        with self.assertRaises(NotFoundError):
            orders.remove_item(order.order_id, 99)
        orders.cancel_order(order.order_id)
        with self.assertRaises(ValidationError):
            orders.add_item(order.order_id, 1, 1)

    def test_search_orders(self):
        self.app.order_service.create_order(1, [(3, 1)])
        self.assertEqual(len(self.app.order_service.search_orders("amok")), 1)
        self.assertEqual(len(self.app.order_service.search_orders("sok")), 1)

    def test_bill_rules_and_payment(self):
        order = self.app.order_service.create_order(1, [(1, 2)])
        bill = self.app.bill_service.generate_bill(order.order_id)
        with self.assertRaises(ValidationError):
            self.app.bill_service.generate_bill(order.order_id)
        with self.assertRaises(ValidationError):
            self.app.bill_service.record_payment(bill.bill_id, "Cash", 5)
        self.app.bill_service.record_payment(bill.bill_id, "Cash", 10)
        self.assertEqual(bill.change, 2.30)
        with self.assertRaises(ValidationError):
            self.app.bill_service.record_payment(bill.bill_id, "Card")
        reloaded = self.reload().bill_service.get_bill(bill.bill_id)
        self.assertEqual((reloaded.status, reloaded.payment_method, reloaded.change), ("Paid", "Cash", 2.30))

    def test_cancelled_order_cannot_be_billed(self):
        order = self.app.order_service.create_order(1, [(1, 1)])
        self.app.order_service.cancel_order(order.order_id)
        with self.assertRaises(ValidationError):
            self.app.bill_service.generate_bill(order.order_id)

    def test_invalid_references(self):
        with self.assertRaises(NotFoundError):
            self.app.order_service.create_order(99, [(1, 1)])
        with self.assertRaises(NotFoundError):
            self.app.order_service.create_order(1, [(99, 1)])
        with self.assertRaises(ValidationError):
            self.app.order_service.create_order(1, [])
        with self.assertRaises(ValidationError):
            self.app.order_service.create_order(1, [(1, 0)])


class ReportTests(BaseTest):
    def paid_order(self, customer_id, selections, method="Card"):
        order = self.app.order_service.create_order(customer_id, selections)
        bill = self.app.bill_service.generate_bill(order.order_id)
        self.app.bill_service.record_payment(bill.bill_id, method)
        return bill

    def test_reports(self):
        self.paid_order(1, [(1, 2)])
        self.paid_order(2, [(6, 1)], "KHQR")
        today = date.today()
        report = self.app.report_service
        daily = report.daily_summary(today)
        self.assertEqual(daily["orders"], 2)
        self.assertEqual(daily["revenue"], round(7.70 + 2.20, 2))
        monthly = report.monthly_summary(today.year, today.month)
        self.assertEqual(monthly["paid_bills"], 2)
        sales = report.sales_report()
        self.assertEqual(sales["quantity"], 3)
        revenue = report.revenue_report()
        self.assertEqual(revenue["revenue"], 9.90)
        self.assertEqual(dict(revenue["by_method"])["KHQR"][0], 1)
        totals = dict(report.total_records())
        self.assertEqual(totals["Orders"], 2)
        self.assertEqual(len(report.order_history(1)), 1)


class StorageTests(BaseTest):
    def test_missing_file_is_recreated(self):
        (self.directory / "orders.json").unlink()
        app = RestaurantApp(self.directory)
        self.assertTrue(any("orders.json" in notice for notice in app.notices))
        self.assertTrue((self.directory / "orders.json").exists())

    def test_damaged_file_is_replaced(self):
        (self.directory / "menu.json").write_text("{ not json", encoding="utf-8")
        app = RestaurantApp(self.directory)
        self.assertEqual(app.menu_service.count(), 10)
        self.assertTrue((self.directory / "menu.json.bak").exists())

    def test_duplicate_ids_in_file_are_ignored(self):
        path = self.directory / "menu.json"
        records = json.loads(path.read_text(encoding="utf-8"))
        records.append(dict(records[0]))
        path.write_text(json.dumps(records), encoding="utf-8")
        app = RestaurantApp(self.directory)
        self.assertEqual(app.menu_service.count(), 10)
        self.assertTrue(any("Duplicate" in notice for notice in app.notices))


class LayoutTests(unittest.TestCase):
    def test_text_is_centered(self):
        with patch("app.utils.layout.term_width", return_value=80):
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                layout.say("hello")
                layout.print_block("ab\nabcd")
            lines = buffer.getvalue().splitlines()
        self.assertEqual(lines[0].strip(), "hello")
        self.assertEqual(lines[1], " " * 38 + "ab")
        self.assertEqual(lines[2], " " * 38 + "abcd")


if __name__ == "__main__":
    unittest.main()
