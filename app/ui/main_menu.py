from app import config
from app.ui import auth_ui, bill_ui, customer_ui, menu_ui, order_ui, report_ui, user_ui
from app.ui.common import user_line
from app.utils import feedback
from app.utils.console import pause, show_menu
from app.utils.exceptions import AppError
from app.utils.layout import say, screen


def startup(app):
    screen(config.APP_TITLE, config.STUDENT_NAME)
    feedback.progress("Loading data")
    for notice in app.notices:
        feedback.warning(notice)
    print()
    feedback.success(
        f"Data ready: {app.menu_service.count()} menu items, "
        f"{len(app.customer_service.get_all_customers())} customers, "
        f"{len(app.order_service.get_all_orders())} orders, "
        f"{len(app.bill_service.get_all_bills())} bills."
    )
    pause()


def session(app):
    entries = [
        ("Menu Management", "Maintain food and drink items", "menu.view", menu_ui.run),
        ("Customer Management", "Select a registered or walk-in customer", "customers", customer_ui.run),
        ("Order Management", "Select items, quantities, and confirm order", "orders", order_ui.run),
        ("Bill Management", "Calculate total and record payment", "bills", bill_ui.run),
        ("Reports", "Summaries, sales, revenue and history", "reports", report_ui.run),
        ("User Management", "Manage staff accounts and roles", "users", user_ui.run),
        ("Change Password", "Update the password of your account", None, auth_ui.change_password),
    ]
    available = [entry for entry in entries if entry[2] is None or app.auth_service.can(entry[2])]
    labels = [entry[0] for entry in available] + ["Logout", "Exit"]
    descriptions = [entry[1] for entry in available] + [
        "Sign out and return to the login screen",
        "Close the application",
    ]
    while True:
        choice = show_menu(
            config.APP_TITLE,
            labels,
            subtitles=[config.STUDENT_NAME, user_line(app)],
            descriptions=descriptions,
        )
        if choice == len(labels):
            return True
        if choice == len(labels) - 1:
            user = app.auth_service.logout()
            app.customer_service.clear_selection()
            feedback.success(f"{user.full_name} was logged out.")
            pause()
            return False
        try:
            available[choice - 1][3](app)
        except AppError as error:
            feedback.error(str(error))
        if available[choice - 1][3] is auth_ui.change_password:
            pause()


def run(app):
    startup(app)
    while True:
        choice = show_menu(
            config.APP_TITLE,
            ["Login", "Exit"],
            subtitles=[config.STUDENT_NAME],
            descriptions=["Sign in with your username and password", "Close the application"],
        )
        if choice == 2:
            screen("GOODBYE")
            say("Thank you for using the Restaurant Ordering System!")
            say()
            return
        if auth_ui.login(app):
            pause()
            if session(app):
                screen("GOODBYE")
                say("Thank you for using the Restaurant Ordering System!")
                say()
                return
        else:
            pause()
