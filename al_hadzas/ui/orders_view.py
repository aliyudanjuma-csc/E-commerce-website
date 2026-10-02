"""
ui/orders_view.py
--------------------
Buyer-facing order history / tracking (FR-11). Also offers a "Leave a
review" action once an order is delivered (FR-09).
"""

import flet as ft

from ui import theme
from ui.state import require_login
from core.data_store import STORE, Review, next_id

STATUS_STEPS = ["placed", "processing", "shipped", "delivered"]


def orders_view(page: ft.Page) -> ft.View:
    session = require_login(page)
    if session is None:
        return ft.View(route="/orders", controls=[ft.ProgressRing()])

    orders = sorted(STORE.buyer_orders(session.user_id), key=lambda o: o.created_at, reverse=True)

    def status_tracker(order) -> ft.Row:
        chips = []
        current_idx = STATUS_STEPS.index(order.status) if order.status in STATUS_STEPS else 0
        for i, step in enumerate(STATUS_STEPS):
            done = i <= current_idx
            chips.append(ft.Container(
                padding=6, border_radius=20,
                bgcolor=theme.SECONDARY if done else "#E0E0E0",
                content=ft.Text(step.capitalize(), size=11, color="white" if done else theme.MUTED),
            ))
        return ft.Row(chips, spacing=6)

    def open_review_dialog(order, item):
        rating_field = ft.Dropdown(
            label="Rating", width=120,
            options=[ft.dropdown.Option(str(i)) for i in range(1, 6)], value="5",
        )
        comment_field = ft.TextField(label="Comment", multiline=True, width=320)

        def submit(e):
            from core.security import sanitize_text
            review = Review(
                id=next_id("REV"), product_id=item.product_id, buyer_id=session.user_id,
                rating=int(rating_field.value), comment=sanitize_text(comment_field.value or "", 500),
            )
            STORE.add_review(review)
            STORE.log_action(session.user_id, "review_submitted", item.product_id)
            page.close(dialog)
            page.go("/orders")

        dialog = ft.AlertDialog(
            title=ft.Text(f"Review {item.name}"),
            content=ft.Column([rating_field, comment_field], tight=True),
            actions=[ft.TextButton("Cancel", on_click=lambda e: page.close(dialog)),
                     ft.TextButton("Submit", on_click=submit)],
        )
        page.open(dialog)

    order_cards = []
    for order in orders:
        vendor = STORE.vendors.get(order.vendor_id)
        item_rows = []
        for item in order.items:
            row_controls = [ft.Text(f"{item.quantity} x {item.name} ({item.size})", size=13, expand=True),
                             ft.Text(f"${item.unit_price*item.quantity:.2f}", size=13)]
            if order.status == "delivered":
                row_controls.append(ft.TextButton("Review", on_click=lambda e, o=order, it=item: open_review_dialog(o, it)))
            item_rows.append(ft.Row(row_controls))

        order_cards.append(theme.section_card(
            ft.Row([
                ft.Text(order.id, weight=ft.FontWeight.BOLD),
                ft.Text(vendor.business_name if vendor else "", size=12, color=theme.MUTED),
                ft.Text(f"${order.total:.2f}", weight=ft.FontWeight.BOLD),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            status_tracker(order),
            ft.Column(item_rows, spacing=4),
        ))

    if not order_cards:
        order_cards = [ft.Text("You have no orders yet.", color=theme.MUTED)]

    return ft.View(
        route="/orders",
        appbar=theme.app_bar(page, "My Orders", session),
        bgcolor=theme.LIGHT_BG,
        scroll=ft.ScrollMode.AUTO,
        controls=[ft.Container(padding=24, content=ft.Column(order_cards, spacing=14))],
    )
