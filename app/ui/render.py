from app import config
from app.utils.colors import paint
from app.utils.tables import render_pairs, render_table


def money(value):
    return f"{config.CURRENCY}{value:,.2f}"


STATUS_STYLES = {
    "Open": ("yellow",),
    "Billed": ("cyan",),
    "Cancelled": ("red",),
    "Paid": ("green", "bold"),
    "Unpaid": ("red",),
    "Active": ("green",),
    "Disabled": ("red",),
}


def status_text(status):
    return paint(status, *STATUS_STYLES.get(status, ()))


def menu_table(items):
    rows = []
    for item in items:
        style = "yellow" if item.category == "Food" else "cyan"
        rows.append([item.item_id, item.name, money(item.price), paint(item.category, style)])
    return render_table(["ID", "Name", "Price", "Category"], rows, ["right", "left", "right", "left"])


def customers_table(customers):
    rows = [
        [c.customer_id, c.name, c.phone, "Walk-in" if c.is_walk_in else "Registered"]
        for c in customers
    ]
    return render_table(["ID", "Name", "Phone", "Type"], rows, ["right", "left", "left", "left"])


def orders_table(orders, show_total=False):
    rows = [
        [
            o.order_id,
            o.customer.name,
            sum(i.quantity for i in o.items),
            money(o.total()),
            status_text(o.status),
            o.created_at.strftime("%Y-%m-%d %H:%M"),
        ]
        for o in orders
    ]
    footers = None
    if show_total:
        valid = [o for o in orders if o.status != "Cancelled"]
        footers = [["", "", "", money(sum(o.total() for o in valid)), "Excl. cancelled", ""]]
    return render_table(
        ["ID", "Customer", "Qty", "Total", "Status", "Created"],
        rows,
        ["right", "left", "right", "right", "left", "left"],
        footers,
    )


def totals_footers(subtotal, tax, total, columns, rate):
    blank = [""] * (columns - 2)
    return [
        blank + ["Subtotal", money(subtotal)],
        blank + [f"Tax ({int(round(rate * 100))}%)", money(tax)],
        blank + ["TOTAL", paint(money(total), "green", "bold")],
    ]


def order_detail(order):
    pairs = [
        ("Order ID", order.order_id),
        ("Customer", order.customer.label),
        ("Status", status_text(order.status)),
        ("Created", order.created_at.strftime("%Y-%m-%d %H:%M")),
    ]
    rows = [
        [i.item_id, i.name, i.quantity, money(i.unit_price), money(i.subtotal)]
        for i in order.items
    ]
    table = render_table(
        ["ID", "Item", "Qty", "Price", "Subtotal"],
        rows,
        ["right", "left", "right", "right", "right"],
        totals_footers(order.subtotal(), order.tax(), order.total(), 5, config.TAX_RATE),
    )
    return render_pairs(pairs) + "\n\n" + table


def bills_table(bills):
    rows = [
        [
            b.bill_id,
            b.order.order_id,
            b.customer.name,
            money(b.total),
            status_text(b.status),
            b.payment_method or "-",
        ]
        for b in bills
    ]
    return render_table(
        ["Bill", "Order", "Customer", "Total", "Status", "Method"],
        rows,
        ["right", "right", "left", "right", "left", "left"],
    )


def bill_detail(bill):
    pairs = [
        ("Bill ID", bill.bill_id),
        ("Order ID", bill.order.order_id),
        ("Date", bill.issued_at.strftime("%Y-%m-%d %H:%M")),
        ("Customer", bill.customer.label),
        ("Phone", bill.customer.phone),
        ("Status", status_text(bill.status)),
    ]
    rows = [
        [line["name"], line["quantity"], money(line["unit_price"]), money(line["subtotal"])]
        for line in bill.lines
    ]
    footers = totals_footers(bill.subtotal, bill.tax, bill.total, 4, bill.tax_rate)
    if bill.is_paid:
        footers += [
            ["", "", "Paid by", bill.payment_method],
            ["", "", "Received", money(bill.amount_paid)],
            ["", "", "Change", money(bill.change)],
        ]
    table = render_table(
        ["Item", "Qty", "Price", "Subtotal"],
        rows,
        ["left", "right", "right", "right"],
        footers,
    )
    return render_pairs(pairs) + "\n\n" + table


def receipt(bill):
    width = 46
    bar = "=" * width
    rule = "-" * width
    lines = [
        bar,
        paint("RESTAURANT ORDERING SYSTEM".center(width), "bold"),
        "Official Receipt".center(width),
        bar,
        f"Bill ID  : {bill.bill_id:<10} Order ID: {bill.order.order_id}",
        f"Date     : {bill.issued_at.strftime('%Y-%m-%d %H:%M')}",
        f"Customer : {bill.customer.name}",
        f"Phone    : {bill.customer.phone}",
        rule,
        f"{'Item':<20}{'Qty':>4}{'Price':>10}{'Total':>12}",
        rule,
    ]
    for line in bill.lines:
        lines.append(
            f"{line['name'][:19]:<20}{line['quantity']:>4}{line['unit_price']:>10.2f}{line['subtotal']:>12.2f}"
        )
    rate = f"Tax ({int(round(bill.tax_rate * 100))}%)"
    lines += [
        rule,
        f"{'Subtotal':<30}{bill.subtotal:>16.2f}",
        f"{rate:<30}{bill.tax:>16.2f}",
        paint(f"{'TOTAL':<30}{bill.total:>16.2f}", "bold"),
    ]
    if bill.is_paid:
        lines += [
            rule,
            f"{'Paid by ' + bill.payment_method:<30}{bill.amount_paid:>16.2f}",
            f"{'Change':<30}{bill.change:>16.2f}",
        ]
    else:
        lines += [rule, paint("** UNPAID **".center(width), "red", "bold")]
    lines += [bar, "Thank you! Please come again.".center(width), bar]
    return "\n".join(lines)


def users_table(users):
    rows = [
        [
            u.user_id,
            u.username,
            u.full_name,
            u.role.title(),
            status_text("Active" if u.active else "Disabled"),
            u.last_login or "-",
        ]
        for u in users
    ]
    return render_table(
        ["ID", "Username", "Full name", "Role", "Status", "Last login"],
        rows,
        ["right", "left", "left", "left", "left", "left"],
    )
