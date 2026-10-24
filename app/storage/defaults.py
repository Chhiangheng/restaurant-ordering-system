from app.utils import clock, security


def default_menu():
    items = [
        ("Fried Rice", 3.50, "Food"),
        ("Beef Lok Lak", 5.50, "Food"),
        ("Fish Amok", 6.00, "Food"),
        ("Chicken Noodle Soup", 4.00, "Food"),
        ("Pork Skewers", 3.00, "Food"),
        ("Iced Coffee", 2.00, "Drink"),
        ("Fresh Orange Juice", 2.50, "Drink"),
        ("Coconut Water", 1.75, "Drink"),
        ("Milk Tea", 2.25, "Drink"),
        ("Bottled Water", 0.75, "Drink"),
    ]
    return [
        {"item_id": index, "name": name, "price": price, "category": category}
        for index, (name, price, category) in enumerate(items, 1)
    ]


def default_customers():
    return [
        {"customer_id": 1, "name": "Sok Dara", "phone": "012 345 678"},
        {"customer_id": 2, "name": "Chan Sreymom", "phone": "098 765 432"},
    ]


def default_users():
    created = clock.format_datetime(clock.now())
    accounts = [
        ("admin", "Admin@123", "admin", "System Administrator"),
        ("manager", "Manager@123", "manager", "Restaurant Manager"),
        ("cashier", "Cashier@123", "cashier", "Front Desk Cashier"),
    ]
    return [
        {
            "user_id": index,
            "username": username,
            "password_hash": security.hash_password(password),
            "role": role,
            "full_name": full_name,
            "active": True,
            "created_at": created,
            "last_login": "",
        }
        for index, (username, password, role, full_name) in enumerate(accounts, 1)
    ]


def empty_list():
    return []
