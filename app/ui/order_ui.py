from app.models.order import Order
from app.ui import render
from app.ui.common import open_screen, run_menu, show_table
from app.ui.customer_ui import current_customer_text, extra_lines, select_customer_flow
from app.utils import feedback
from app.utils.exceptions import AppError
from app.utils.console import show_menu
from app.utils.layout import print_block, say, screen
from app.utils.validators import confirm, read_int, read_text


def show_orders(orders, show_total=False):
    if not orders:
        feedback.info("No orders found.")
        return
    show_table(render.orders_table(orders, show_total), len(orders), "order")


def create_order(app):
    open_screen(app, "CREATE NEW ORDER", current_customer_text(app))
    customer = app.customer_service.current_customer
    if customer is None:
        feedback.warning("No customer selected yet.")
        print()
        customer = select_customer_flow(app)
        if customer is None:
            feedback.info("Order not created: no customer selected.")
            return
    else:
        say(f"Customer: {customer.label}", "bold")
    items = app.menu_service.get_all_items()
    if not items:
        feedback.error("The menu is empty. Add menu items first.")
        return
    say("\nMenu\n", "bold")
    print_block(render.menu_table(items))
    say("\nEnter item IDs to add. Press Enter on the item ID when finished.\n", "dim")
    selections = []
    while True:
        item_id = read_int("Item ID: ", 1, allow_blank=True)
        if item_id is None:
            break
        item = app.menu_service.get_item(item_id)
        if item is None:
            feedback.error("Item not found.")
            continue
        quantity = read_int(f"Quantity of {item.name}: ", 1, 99)
        selections.append((item_id, quantity))
        feedback.success(f"Added {quantity} x {item.name}")
    if not selections:
        feedback.info("No items selected. Order was not created.")
        return
    preview = app.order_service.preview_order(customer.customer_id, selections)
    open_screen(app, "CONFIRM ORDER")
    print_block(render.order_detail(preview))
    if confirm("\nConfirm this order?"):
        order = app.order_service.create_order(customer.customer_id, selections)
        feedback.success(f"Order #{order.order_id} was confirmed and saved.")
        say(f"{customer.name} stays selected for the next order.", "dim")
    else:
        feedback.info("Order discarded. Nothing was saved.")


def view_orders(app):
    open_screen(app, "ALL ORDERS")
    show_orders(app.order_service.get_all_orders(), show_total=True)


def view_order(app):
    open_screen(app, "ORDER DETAILS")
    show_orders(app.order_service.get_all_orders())
    order = app.order_service.require_order(read_int("\nEnter order ID: ", 1))
    print()
    print_block(render.order_detail(order))


def search_orders(app):
    open_screen(app, "SEARCH ORDERS")
    keyword = read_text("Search (order ID, customer, status or item): ")
    print()
    show_orders(app.order_service.search_orders(keyword), show_total=True)


def update_order(app):
    service = app.order_service
    open_screen(app, "UPDATE ORDER")
    show_orders([o for o in service.get_all_orders() if o.status == Order.OPEN])
    order = service.require_order(read_int("\nEnter order ID to update: ", 1))
    if order.status != Order.OPEN:
        feedback.error(f"Order {order.order_id} is {order.status} and cannot be changed.")
        return
    options = ["Add item", "Change item quantity", "Remove item", "Done"]
    message = ("", "")
    while True:
        open_screen(app, f"UPDATE ORDER #{order.order_id}")
        print_block(render.order_detail(order))
        print()
        if message[0]:
            (feedback.success if message[1] == "ok" else feedback.error)(message[0])
            print()
        choice = show_menu("", options, show_header=False)
        message = ("", "")
        try:
            if choice == 1:
                print()
                print_block(render.menu_table(app.menu_service.get_all_items()))
                item_id = read_int("\nItem ID: ", 1)
                app.menu_service.require_item(item_id)
                service.add_item(order.order_id, item_id, read_int("Quantity: ", 1, 99))
                message = ("Item added.", "ok")
            elif choice == 2:
                item_id = read_int("\nItem ID in this order: ", 1)
                service.update_item_quantity(order.order_id, item_id, read_int("New quantity: ", 1, 99))
                message = ("Quantity updated.", "ok")
            elif choice == 3:
                service.remove_item(order.order_id, read_int("\nItem ID to remove: ", 1))
                message = ("Item removed.", "ok")
            else:
                return
        except AppError as error:
            message = (str(error), "error")


def cancel_order(app):
    service = app.order_service
    open_screen(app, "CANCEL ORDER")
    show_orders([o for o in service.get_all_orders() if o.status == Order.OPEN])
    order = service.require_order(read_int("\nEnter order ID to cancel: ", 1))
    if confirm(f"\nCancel order {order.order_id}?"):
        service.cancel_order(order.order_id)
        feedback.success("Order cancelled.")
    else:
        feedback.info("Cancel aborted.")


def change_customer(app):
    open_screen(app, "CHANGE CUSTOMER", current_customer_text(app))
    select_customer_flow(app)


def run(app):
    actions = [
        ("Create New Order", create_order),
        ("View All Orders", view_orders),
        ("View Order Details", view_order),
        ("Search Orders", search_orders),
        ("Update Order", update_order),
        ("Cancel Order", cancel_order),
        ("Change Customer", change_customer),
    ]
    run_menu(app, "ORDER MANAGEMENT", actions, extra_lines)
