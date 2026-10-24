from app.ui import render
from app.ui.common import open_screen, run_menu, show_table
from app.models.user import ROLES
from app.utils import feedback
from app.utils.console import show_menu
from app.utils.layout import say
from app.utils.validators import confirm, read_int, read_new_password, read_text, read_username


def show_users(users):
    if not users:
        feedback.info("No users found.")
        return
    show_table(render.users_table(users), len(users), "user")


def read_role(prompt="Role"):
    say(f"{prompt}\n", "bold")
    return ROLES[show_menu("", [role.title() for role in ROLES], show_header=False) - 1]


def list_users(app):
    open_screen(app, "ALL USERS")
    show_users(app.auth_service.get_all_users())


def search_users(app):
    open_screen(app, "SEARCH USERS")
    keyword = read_text("Search (ID, username, name or role): ")
    print()
    show_users(app.auth_service.search_users(keyword))


def add_user(app):
    open_screen(app, "ADD USER")
    app.auth_service.require("users")
    username = read_username("Username: ")
    full_name = read_text("Full name: ")
    print()
    role = read_role()
    print()
    password = read_new_password()
    user = app.auth_service.add_user(username, password, role, full_name)
    feedback.success(f"User '{user.username}' was created as {user.role}.")


def update_user(app):
    open_screen(app, "UPDATE USER")
    show_users(app.auth_service.get_all_users())
    user = app.auth_service.require_user(read_int("\nEnter user ID to update: ", 1))
    feedback.info(f"Updating {user.username}. Press Enter to keep a value.")
    print()
    full_name = read_text(f"Full name [{user.full_name}]: ", allow_blank=True) or None
    role = None
    if confirm(f"Change role (currently {user.role})?"):
        role = read_role("New role")
    active = None
    if confirm(f"Account is {'active' if user.active else 'disabled'}. Toggle status?"):
        active = not user.active
    app.auth_service.update_user(user.user_id, full_name, role, active)
    feedback.success("User updated.")


def reset_password(app):
    open_screen(app, "RESET PASSWORD")
    show_users(app.auth_service.get_all_users())
    user = app.auth_service.require_user(read_int("\nEnter user ID: ", 1))
    print()
    password = read_new_password()
    app.auth_service.reset_password(user.user_id, password)
    feedback.success(f"Password for '{user.username}' was changed.")


def delete_user(app):
    open_screen(app, "DELETE USER")
    show_users(app.auth_service.get_all_users())
    user = app.auth_service.require_user(read_int("\nEnter user ID to delete: ", 1))
    if confirm(f"\nDelete user '{user.username}'?"):
        app.auth_service.delete_user(user.user_id)
        feedback.success("User deleted.")
    else:
        feedback.info("Delete cancelled.")


def run(app):
    actions = [
        ("View All Users", list_users),
        ("Search Users", search_users),
        ("Add User", add_user),
        ("Update User", update_user),
        ("Reset Password", reset_password),
        ("Delete User", delete_user),
    ]
    run_menu(app, "USER MANAGEMENT", actions)
