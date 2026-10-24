from app.ui import render
from app.ui.common import open_screen, run_menu, show_table
from app.utils import feedback
from app.utils.console import show_menu
from app.utils.layout import say
from app.utils.validators import confirm, read_int, read_name, read_phone, read_text


def current_customer_text(app):
    customer = app.customer_service.current_customer
    if customer is None:
        return "Current customer: none selected"
    return f"Current customer: {customer.label}"


def extra_lines(app):
    return [current_customer_text(app)]


def show_customers(customers):
    if not customers:
        feedback.info("No customers found.")
        return
    show_table(render.customers_table(customers), len(customers), "customer")


def register(app):
    open_screen(app, "REGISTER CUSTOMER")
    name = read_name("Customer name: ")
    phone = read_phone("Phone number: ")
    customer = app.customer_service.register_customer(name, phone)
    feedback.success(f"{customer.name} was registered with ID {customer.customer_id}.")
    if confirm("\nSelect this customer for new orders?"):
        app.customer_service.select_customer(customer.customer_id)
        feedback.success(f"{customer.name} is now the current customer.")


def display_all(app):
    open_screen(app, "ALL CUSTOMERS")
    say("Registered customers\n", "bold")
    show_customers(app.customer_service.get_all_customers())
    walk_ins = app.customer_service.get_walk_in_customers()
    if walk_ins:
        say("\nWalk-in customers\n", "bold")
        show_customers(walk_ins)


def search(app):
    open_screen(app, "SEARCH CUSTOMER")
    keyword = read_text("Enter customer ID, name or phone: ")
    print()
    show_customers(app.customer_service.search_customers(keyword))


def update(app):
    open_screen(app, "UPDATE CUSTOMER")
    show_customers(app.customer_service.get_all_customers())
    customer = app.customer_service.require_customer(read_int("\nEnter customer ID to update: ", 1))
    feedback.info(f"Updating {customer.name}. Press Enter to keep a value.")
    print()
    name = read_name(f"Name [{customer.name}]: ", allow_blank=True)
    phone = read_phone(f"Phone [{customer.phone}]: ", allow_blank=True)
    app.customer_service.update_customer(customer.customer_id, name, phone)
    feedback.success("Customer updated.")


def delete(app):
    open_screen(app, "DELETE CUSTOMER")
    show_customers(app.customer_service.get_all_customers())
    customer = app.customer_service.require_customer(read_int("\nEnter customer ID to delete: ", 1))
    if confirm(f"\nDelete {customer.name}?"):
        app.customer_service.delete_customer(customer.customer_id)
        feedback.success("Customer deleted.")
    else:
        feedback.info("Delete cancelled.")


def select_customer_flow(app):
    service = app.customer_service
    say("Who is the customer?\n", "bold")
    options = ["Registered customer", "Walk-in customer (ID is generated automatically)", "Cancel"]
    choice = show_menu("", options, show_header=False)
    if choice == 3:
        return None
    if choice == 2:
        customer = service.select_new_walk_in()
        print()
        feedback.success(f"New walk-in customer created with ID {customer.customer_id}.")
        return customer
    print()
    show_customers(service.get_all_customers())
    while True:
        customer = service.get_customer(read_int("\nEnter customer ID: ", 1))
        if customer:
            break
        feedback.error("Customer not found.")
    service.select_customer(customer.customer_id)
    print()
    feedback.success(f"{customer.label} is now the current customer.")
    return customer


def select(app):
    open_screen(app, "SELECT CUSTOMER", current_customer_text(app))
    customer = select_customer_flow(app)
    if customer is None:
        return
    orders = app.order_service.get_orders_for_customer(customer.customer_id)
    say("\nOrder history\n", "bold")
    if orders:
        show_table(render.orders_table(orders), len(orders), "order")
    else:
        feedback.info("No orders yet.")
    say("\nGo to Order Management to create an order for this customer.", "dim")


def run(app):
    actions = [
        ("Register New Customer", register),
        ("Display All Customers", display_all),
        ("Search Customer (ID, name or phone)", search),
        ("Update Customer", update),
        ("Delete Customer", delete),
        ("Select Customer (registered or walk-in)", select),
    ]
    run_menu(app, "CUSTOMER MANAGEMENT", actions, extra_lines)
