from app.models.bill import Bill
from app.models.order import Order
from app.ui import render
from app.ui.common import open_screen, run_menu, show_table
from app.ui.order_ui import show_orders
from app.utils import feedback
from app.utils.exceptions import AppError
from app.utils.console import show_menu
from app.utils.layout import print_block, say
from app.utils.validators import confirm, read_int, read_price, read_text


def show_bills(bills):
    if not bills:
        feedback.info("No bills found.")
        return
    show_table(render.bills_table(bills), len(bills), "bill")


def take_payment(app, bill):
    say(f"\nTotal to pay: {render.money(bill.total)}\n", "bold")
    say("Select payment method\n", "bold")
    methods = list(Bill.PAYMENT_METHODS)
    method = methods[show_menu("", methods, show_header=False) - 1]
    if method == "Cash":
        while True:
            amount = read_price("\nAmount received: ")
            try:
                app.bill_service.record_payment(bill.bill_id, method, amount)
                break
            except AppError as error:
                feedback.error(str(error))
    else:
        app.bill_service.record_payment(bill.bill_id, method)
    print()
    feedback.progress("Recording payment")
    open_screen(app, f"PAYMENT RECORDED - BILL #{bill.bill_id}")
    print_block(render.bill_detail(bill))
    print()
    feedback.success("Payment recorded.")


def generate(app):
    open_screen(app, "GENERATE BILL")
    waiting = [o for o in app.order_service.get_all_orders() if o.status == Order.OPEN]
    say("Orders waiting for a bill\n", "bold")
    show_orders(waiting)
    if not waiting:
        return
    order_id = read_int("\nEnter order ID: ", 1)
    print()
    feedback.progress("Calculating total")
    bill = app.bill_service.generate_bill(order_id)
    open_screen(app, f"BILL #{bill.bill_id} GENERATED")
    print_block(render.bill_detail(bill))
    print()
    feedback.success(f"Bill #{bill.bill_id} was generated.")
    if confirm("\nRecord payment now?"):
        take_payment(app, bill)


def record_payment(app):
    open_screen(app, "RECORD PAYMENT")
    unpaid = app.bill_service.get_unpaid_bills()
    say("Unpaid bills\n", "bold")
    show_bills(unpaid)
    if not unpaid:
        return
    bill = app.bill_service.require_bill(read_int("\nEnter bill ID: ", 1))
    if bill.is_paid:
        feedback.error("This bill is already paid.")
        return
    print()
    print_block(render.bill_detail(bill))
    take_payment(app, bill)


def pick_bill(app, title):
    open_screen(app, title)
    bills = app.bill_service.get_all_bills()
    show_bills(bills)
    if not bills:
        return None
    return app.bill_service.require_bill(read_int("\nEnter bill ID: ", 1))


def view_bill(app):
    bill = pick_bill(app, "VIEW BILL")
    if bill:
        print()
        print_block(render.bill_detail(bill))


def print_bill(app):
    bill = pick_bill(app, "PRINT BILL")
    if bill:
        print()
        feedback.progress("Preparing receipt")
        print()
        print_block(render.receipt(bill))


def all_bills(app):
    open_screen(app, "ALL BILLS")
    show_bills(app.bill_service.get_all_bills())


def search_bills(app):
    open_screen(app, "SEARCH BILLS")
    keyword = read_text("Search (bill ID, order ID, customer, Paid/Unpaid or method): ")
    print()
    show_bills(app.bill_service.search_bills(keyword))


def run(app):
    actions = [
        ("Generate Bill for an Order", generate),
        ("Record Payment", record_payment),
        ("View Bill", view_bill),
        ("Print Bill", print_bill),
        ("View All Bills", all_bills),
        ("Search Bills", search_bills),
    ]
    run_menu(app, "BILL MANAGEMENT", actions)
