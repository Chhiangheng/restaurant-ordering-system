from datetime import date

from app.ui import render
from app.ui.common import open_screen, run_menu, show_table
from app.utils import feedback, rules
from app.utils.exceptions import ValidationError
from app.utils.layout import print_block, say
from app.utils.tables import render_pairs, render_table
from app.utils.validators import read_date, read_month, read_text, read_validated

money = render.money


def total_records(app):
    open_screen(app, "TOTAL RECORDS")
    rows = app.report_service.total_records()
    feedback.progress("Generating report")
    print()
    print_block(render_table(["Record type", "Total"], [[name, count] for name, count in rows], ["left", "right"]))


def daily_summary(app):
    open_screen(app, "DAILY SUMMARY")
    day = read_date("Date (YYYY-MM-DD, Enter for today): ", date.today())
    report = app.report_service.daily_summary(day)
    feedback.progress("Generating report")
    print()
    pairs = [
        ("Date", report["date"].isoformat()),
        ("Orders created", report["orders"]),
        ("Open / Billed / Cancelled", f"{report['open']} / {report['billed']} / {report['cancelled']}"),
        ("Paid bills", report["paid_bills"]),
        ("Items sold", report["items_sold"]),
        ("Sales (before tax)", money(report["subtotal"])),
        ("Tax collected", money(report["tax"])),
        ("Revenue", money(report["revenue"])),
    ]
    print_block(render_pairs(pairs))
    say("\nTop selling items\n", "bold")
    if report["top_items"]:
        rows = [[name, qty, money(sales)] for name, qty, sales in report["top_items"]]
        print_block(render_table(["Item", "Qty", "Sales"], rows, ["left", "right", "right"]))
    else:
        feedback.info("No paid sales on this date.")


def monthly_summary(app):
    open_screen(app, "MONTHLY SUMMARY")
    today = date.today()
    year, month = read_month("Month (YYYY-MM, Enter for this month): ", (today.year, today.month))
    report = app.report_service.monthly_summary(year, month)
    feedback.progress("Generating report")
    print()
    best = report["best_day"]
    pairs = [
        ("Month", f"{year:04d}-{month:02d}"),
        ("Orders created", report["orders"]),
        ("Cancelled orders", report["cancelled"]),
        ("Paid bills", report["paid_bills"]),
        ("Revenue", money(report["revenue"])),
        ("Average per active day", money(report["average_per_day"])),
        ("Best day", f"{best['date'].isoformat()} ({money(best['revenue'])})" if best else "-"),
    ]
    print_block(render_pairs(pairs))
    if not report["rows"]:
        print()
        feedback.info("No activity in this month.")
        return
    say("\nDaily breakdown\n", "bold")
    rows = [[r["date"].isoformat(), r["orders"], r["paid_bills"], money(r["revenue"])] for r in report["rows"]]
    footers = [["Total", report["orders"], report["paid_bills"], money(report["revenue"])]]
    print_block(render_table(["Date", "Orders", "Paid bills", "Revenue"], rows,
                             ["left", "right", "right", "right"], footers))


def sales_report(app):
    open_screen(app, "SALES REPORT")
    say("Leave both dates empty to include all sales.\n", "dim")
    start = read_validated("From date (YYYY-MM-DD, Enter to skip): ", rules.check_date, allow_blank=True)
    end = read_validated("To date (YYYY-MM-DD, Enter to skip): ", rules.check_date, allow_blank=True)
    if start and end and start > end:
        raise ValidationError("The start date must not be after the end date.")
    report = app.report_service.sales_report(start, end)
    feedback.progress("Generating report")
    print()
    if not report["rows"]:
        feedback.info("No paid sales found for this period.")
        return
    rows = [[r["name"], r["quantity"], money(r["sales"]), f"{r['share']:.1f}%"] for r in report["rows"]]
    footers = [["Total", report["quantity"], money(report["sales"]), "100.0%"]]
    print_block(render_table(["Item", "Qty sold", "Sales", "Share"], rows,
                             ["left", "right", "right", "right"], footers))
    say(f"\nBased on {report['bills']} paid bill(s).", "dim")


def revenue_report(app):
    open_screen(app, "REVENUE REPORT")
    report = app.report_service.revenue_report()
    feedback.progress("Generating report")
    print()
    pairs = [
        ("Paid bills", report["paid_bills"]),
        ("Sales (before tax)", money(report["subtotal"])),
        ("Tax collected", money(report["tax"])),
        ("Total revenue", money(report["revenue"])),
        ("Average bill", money(report["average"])),
        ("Unpaid bills", f"{report['unpaid_bills']} ({money(report['outstanding'])} outstanding)"),
    ]
    print_block(render_pairs(pairs))
    if report["by_method"]:
        say("\nRevenue by payment method\n", "bold")
        rows = [[name, count, money(total)] for name, (count, total) in report["by_method"]]
        print_block(render_table(["Method", "Bills", "Revenue"], rows, ["left", "right", "right"]))
    if report["by_month"]:
        say("\nRevenue by month\n", "bold")
        rows = [[name, count, money(total)] for name, (count, total) in report["by_month"]]
        print_block(render_table(["Month", "Bills", "Revenue"], rows, ["left", "right", "right"]))


def order_history(app):
    open_screen(app, "ORDER HISTORY REPORT")
    say("Enter a customer ID (for example 1 or W001), or press Enter for all customers.\n", "dim")
    text = read_text("Customer ID: ", allow_blank=True)
    customer_id = None
    if text:
        customer = app.customer_service.find_by_text(text)
        customer_id = customer.customer_id if customer else text
    orders = app.report_service.order_history(customer_id)
    feedback.progress("Generating report")
    print()
    if not orders:
        feedback.info("No orders found.")
        return
    show_table(render.orders_table(orders, show_total=True), len(orders), "order")


def run(app):
    actions = [
        ("Total Records", total_records),
        ("Daily Summary", daily_summary),
        ("Monthly Summary", monthly_summary),
        ("Sales Report", sales_report),
        ("Revenue Report", revenue_report),
        ("Order History", order_history),
    ]
    run_menu(app, "REPORTS", actions)
