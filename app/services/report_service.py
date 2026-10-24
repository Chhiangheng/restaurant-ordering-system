import calendar
from datetime import date


class ReportService:
    def __init__(self, auth_service, menu_service, customer_service, order_service, bill_service):
        self.__auth = auth_service
        self.__menu = menu_service
        self.__customers = customer_service
        self.__orders = order_service
        self.__bills = bill_service

    def __paid_bills(self, start=None, end=None):
        result = []
        for bill in self.__bills.get_all_bills():
            if not bill.is_paid:
                continue
            paid_day = bill.paid_at.date()
            if start is not None and paid_day < start:
                continue
            if end is not None and paid_day > end:
                continue
            result.append(bill)
        return result

    @staticmethod
    def __item_totals(bills):
        totals = {}
        for bill in bills:
            for line in bill.lines:
                entry = totals.setdefault(line["name"], [0, 0.0])
                entry[0] += line["quantity"]
                entry[1] = round(entry[1] + line["subtotal"], 2)
        return totals

    def total_records(self):
        self.__auth.require("reports")
        orders = self.__orders.get_all_orders()
        bills = self.__bills.get_all_bills()
        return [
            ("Menu items", self.__menu.count()),
            ("Registered customers", len(self.__customers.get_all_customers())),
            ("Walk-in customers", len(self.__customers.get_walk_in_customers())),
            ("Orders", len(orders)),
            ("Bills", len(bills)),
            ("Paid bills", sum(1 for bill in bills if bill.is_paid)),
            ("User accounts", self.__auth.count_users()),
        ]

    def daily_summary(self, day):
        self.__auth.require("reports")
        orders = [o for o in self.__orders.get_all_orders() if o.created_at.date() == day]
        bills = self.__paid_bills(day, day)
        items = self.__item_totals(bills)
        ranked = sorted(items.items(), key=lambda pair: (-pair[1][0], pair[0]))
        return {
            "date": day,
            "orders": len(orders),
            "open": sum(1 for o in orders if o.status == "Open"),
            "billed": sum(1 for o in orders if o.status == "Billed"),
            "cancelled": sum(1 for o in orders if o.status == "Cancelled"),
            "paid_bills": len(bills),
            "items_sold": sum(entry[0] for entry in items.values()),
            "subtotal": round(sum(b.subtotal for b in bills), 2),
            "tax": round(sum(b.tax for b in bills), 2),
            "revenue": round(sum(b.total for b in bills), 2),
            "top_items": [(name, entry[0], entry[1]) for name, entry in ranked[:5]],
        }

    def monthly_summary(self, year, month):
        self.__auth.require("reports")
        days_in_month = calendar.monthrange(year, month)[1]
        first, last = date(year, month, 1), date(year, month, days_in_month)
        orders = [o for o in self.__orders.get_all_orders() if first <= o.created_at.date() <= last]
        bills = self.__paid_bills(first, last)
        rows = []
        for number in range(1, days_in_month + 1):
            day = date(year, month, number)
            day_orders = [o for o in orders if o.created_at.date() == day]
            day_bills = [b for b in bills if b.paid_at.date() == day]
            if day_orders or day_bills:
                rows.append({
                    "date": day,
                    "orders": len(day_orders),
                    "paid_bills": len(day_bills),
                    "revenue": round(sum(b.total for b in day_bills), 2),
                })
        best = max(rows, key=lambda row: row["revenue"]) if rows else None
        revenue = round(sum(b.total for b in bills), 2)
        return {
            "year": year,
            "month": month,
            "rows": rows,
            "orders": len(orders),
            "cancelled": sum(1 for o in orders if o.status == "Cancelled"),
            "paid_bills": len(bills),
            "revenue": revenue,
            "average_per_day": round(revenue / len(rows), 2) if rows else 0.0,
            "best_day": best,
        }

    def sales_report(self, start=None, end=None):
        self.__auth.require("reports")
        bills = self.__paid_bills(start, end)
        totals = self.__item_totals(bills)
        grand = round(sum(entry[1] for entry in totals.values()), 2)
        rows = []
        for name, entry in sorted(totals.items(), key=lambda pair: (-pair[1][1], pair[0])):
            share = entry[1] / grand * 100 if grand else 0.0
            rows.append({"name": name, "quantity": entry[0], "sales": entry[1], "share": share})
        return {
            "start": start,
            "end": end,
            "rows": rows,
            "bills": len(bills),
            "quantity": sum(row["quantity"] for row in rows),
            "sales": grand,
        }

    def revenue_report(self):
        self.__auth.require("reports")
        all_bills = self.__bills.get_all_bills()
        paid = self.__paid_bills()
        by_method = {}
        by_month = {}
        for bill in paid:
            method = by_method.setdefault(bill.payment_method, [0, 0.0])
            method[0] += 1
            method[1] = round(method[1] + bill.total, 2)
            key = bill.paid_at.strftime("%Y-%m")
            month = by_month.setdefault(key, [0, 0.0])
            month[0] += 1
            month[1] = round(month[1] + bill.total, 2)
        revenue = round(sum(b.total for b in paid), 2)
        return {
            "paid_bills": len(paid),
            "revenue": revenue,
            "subtotal": round(sum(b.subtotal for b in paid), 2),
            "tax": round(sum(b.tax for b in paid), 2),
            "average": round(revenue / len(paid), 2) if paid else 0.0,
            "outstanding": round(sum(b.total for b in all_bills if not b.is_paid), 2),
            "unpaid_bills": sum(1 for b in all_bills if not b.is_paid),
            "by_method": sorted(by_method.items()),
            "by_month": sorted(by_month.items()),
        }

    def order_history(self, customer_id=None):
        self.__auth.require("reports")
        if customer_id is None:
            return self.__orders.get_all_orders()
        self.__customers.require_customer(customer_id)
        return self.__orders.get_orders_for_customer(customer_id)
