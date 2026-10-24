from app.ui import render
from app.ui.common import open_screen, run_menu, show_table
from app.utils import feedback
from app.utils.validators import confirm, read_category, read_int, read_price, read_text


def show_items(items):
    if not items:
        feedback.info("No menu items found.")
        return
    show_table(render.menu_table(items), len(items), "item")


def view_menu(app):
    open_screen(app, "MENU ITEMS")
    show_items(app.menu_service.get_all_items())


def search_menu(app):
    open_screen(app, "SEARCH MENU")
    keyword = read_text("Search (ID, name or category): ")
    print()
    show_items(app.menu_service.search_items(keyword))


def add_item(app):
    open_screen(app, "ADD MENU ITEM")
    name = read_text("Item name: ")
    price = read_price("Price: ")
    category = read_category()
    item = app.menu_service.add_item(name, price, category)
    feedback.success(f"Item #{item.item_id} '{item.name}' was added.")


def update_item(app):
    open_screen(app, "UPDATE MENU ITEM")
    show_items(app.menu_service.get_all_items())
    item = app.menu_service.require_item(read_int("\nEnter item ID to update: ", 1))
    feedback.info(f"Updating '{item.name}'. Press Enter to keep a value.")
    print()
    name = read_text(f"Name [{item.name}]: ", allow_blank=True) or None
    price = read_price(f"Price [{item.price:.2f}]: ", allow_blank=True)
    category = read_category(allow_blank=True)
    app.menu_service.update_item(item.item_id, name, price, category)
    feedback.success("Menu item updated.")


def delete_item(app):
    open_screen(app, "DELETE MENU ITEM")
    show_items(app.menu_service.get_all_items())
    item = app.menu_service.require_item(read_int("\nEnter item ID to delete: ", 1))
    if confirm(f"\nDelete '{item.name}'?"):
        app.menu_service.delete_item(item.item_id)
        feedback.success("Menu item deleted.")
    else:
        feedback.info("Delete cancelled.")


def run(app):
    actions = [("View Menu", view_menu), ("Search Menu Item", search_menu)]
    if app.auth_service.can("menu.edit"):
        actions += [
            ("Add Menu Item", add_item),
            ("Update Menu Item", update_item),
            ("Delete Menu Item", delete_item),
        ]
    run_menu(app, "MENU MANAGEMENT", actions)
