"""
ui/admin_dashboard.py
--------------------------
Admin dashboard (FR-08, FR-12): vendor verification queue, revenue/order
analytics charts, and the OWASP A09 audit log viewer.

Analytics complexity: every aggregate below is a single O(n) pass over
orders/products, and "top sellers" uses heapq.nlargest for O(n log k)
top-k selection rather than a full O(n log n) sort.
"""

import heapq
from collections import defaultdict

import flet as ft

from ui import theme
from ui.state import require_login
from core.data_store import STORE
from core.security import require_role


def admin_dashboard(page: ft.Page) -> ft.View:
    session = require_login(page)
    if session is None:
        return ft.View(route="/admin", controls=[ft.ProgressRing()])

    if not require_role(session, {"admin"}):
        return ft.View(route="/admin", controls=[ft.Text("Access denied: admin accounts only.")])

    # ---- Aggregation (O(n) over orders) ----
    revenue_by_status = defaultdict(float)
    orders_by_status = defaultdict(int)
    revenue_by_product = defaultdict(float)
    product_names = {}

    for order in STORE.orders.values():
        revenue_by_status[order.status] += order.total
        orders_by_status[order.status] += 1
        for item in order.items:
            revenue_by_product[item.product_id] += item.unit_price * item.quantity
            product_names[item.product_id] = item.name

    total_revenue = sum(o.total for o in STORE.orders.values())
    total_commission = sum(o.commission_fee for o in STORE.orders.values())
    total_orders = len(STORE.orders)
    total_products = len(STORE.products)
    total_vendors = len(STORE.vendors)
    verified_vendors = sum(1 for v in STORE.vendors.values() if v.verified)

    # Top 5 products by revenue -> O(n log k), k=5
    top_products = heapq.nlargest(5, revenue_by_product.items(), key=lambda kv: kv[1])

    # ---- KPI cards ----
    def kpi_card(label, value, icon):
        return ft.Container(
            col={"sm": 6, "md": 3},
            content=ft.Card(content=ft.Container(
                padding=16,
                content=ft.Column([
                    ft.Row([ft.Icon(icon, color=theme.PRIMARY), ft.Text(label, size=12, color=theme.MUTED)]),
                    ft.Text(str(value), size=22, weight=ft.FontWeight.BOLD),
                ]),
            )),
        )

    kpi_row = ft.ResponsiveRow([
        kpi_card("Total revenue", f"${total_revenue:.2f}", ft.Icons.PAYMENTS),
        kpi_card("Platform commission", f"${total_commission:.2f}", ft.Icons.ACCOUNT_BALANCE_WALLET),
        kpi_card("Orders", total_orders, ft.Icons.RECEIPT_LONG),
        kpi_card("Products / Vendors", f"{total_products} / {verified_vendors}/{total_vendors}", ft.Icons.STORE),
    ])

    # ---- Orders-by-status bar chart ----
    statuses = ["placed", "processing", "shipped", "delivered"]
    max_count = max(orders_by_status.values(), default=1)
    bar_chart = ft.BarChart(
        bar_groups=[
            ft.BarChartGroup(
                x=i,
                bar_rods=[ft.BarChartRod(
                    from_y=0, to_y=orders_by_status.get(s, 0), width=32,
                    color=theme.PRIMARY, tooltip=f"{s}: {orders_by_status.get(s, 0)}",
                    border_radius=4,
                )],
            ) for i, s in enumerate(statuses)
        ],
        bottom_axis=ft.ChartAxis(labels=[
            ft.ChartAxisLabel(value=i, label=ft.Text(s.capitalize(), size=11)) for i, s in enumerate(statuses)
        ]),
        max_y=max(max_count + 1, 4),
        interactive=True,
        expand=True,
    )

    # ---- Revenue-by-product pie chart ----
    palette = [theme.PRIMARY, theme.SECONDARY, theme.ACCENT, "#8E24AA", "#1565C0"]
    pie_sections = [
        ft.PieChartSection(
            value=rev, title=f"{product_names.get(pid, pid)[:12]}",
            color=palette[i % len(palette)], radius=70, title_style=ft.TextStyle(size=10, color="white"),
        )
        for i, (pid, rev) in enumerate(top_products)
    ] or [ft.PieChartSection(value=1, title="No sales yet", color="#CCCCCC")]

    pie_chart = ft.PieChart(sections=pie_sections, sections_space=2, center_space_radius=30, expand=True)

    # ---- Vendor verification queue ----
    vendor_rows = []
    for v in STORE.vendors.values():
        def make_approve(vid):
            def handler(e):
                vendor = STORE.vendors[vid]
                vendor.verified = True
                STORE.log_action(session.user_id, "vendor_verified", vid)
                page.go("/admin")
            return handler

        vendor_rows.append(ft.Row([
            ft.Text(v.business_name, expand=True), ft.Text(v.country, size=12, color=theme.MUTED),
            ft.Text("✅ Verified" if v.verified else "⏳ Pending", color=theme.SECONDARY if v.verified else theme.DANGER),
            ft.TextButton("Approve", on_click=make_approve(v.id), disabled=v.verified),
        ]))

    # ---- Audit log (most recent first) ----
    audit_rows = [
        ft.Text(f"{e['action']} — actor {e['actor_id']} — {e['detail']}", size=11, color=theme.MUTED)
        for e in reversed(STORE.audit_log[-20:])
    ] or [ft.Text("No activity yet.", size=12, color=theme.MUTED)]

    return ft.View(
        route="/admin",
        appbar=theme.app_bar(page, "Admin Dashboard", session),
        bgcolor=theme.LIGHT_BG,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                padding=24,
                content=ft.Column([
                    kpi_row,
                    ft.ResponsiveRow([
                        ft.Container(col={"sm": 12, "md": 6}, content=theme.section_card(
                            theme.heading("Orders by status", size=16),
                            ft.Container(bar_chart, height=240),
                        )),
                        ft.Container(col={"sm": 12, "md": 6}, content=theme.section_card(
                            theme.heading("Top products by revenue", size=16),
                            ft.Container(pie_chart, height=240),
                        )),
                    ]),
                    theme.section_card(
                        theme.heading("Vendor verification", size=16),
                        ft.Column(vendor_rows, spacing=6),
                    ),
                    theme.section_card(
                        theme.heading("Audit log (security & activity)", size=16),
                        ft.Column(audit_rows, spacing=2),
                    ),
                ], spacing=16),
            )
        ],
    )
