"""
ui/cart_view.py
------------------
Shopping cart: lists items from page.session cart, lets the buyer
adjust/remove items, and shows a live cost breakdown preview using the
same core.payment.compute_cost_breakdown() used at checkout (single
source of truth for pricing math).
"""

import flet as ft

from ui import theme
from ui.state import require_login, get_cart, remove_from_cart, cart_order_items
from core.data_store import STORE
from core.payment import compute_cost_breakdown


def cart_view(page: ft.Page) -> ft.View:
    session = require_login(page)
    if session is None:
        return ft.View(route="/cart", controls=[ft.ProgressRing()])

    items_column = ft.Column(spacing=10)
    summary_column = ft.Column(spacing=4)

    def render():
        cart = get_cart(page)
        items_column.controls.clear()
        if not cart:
            items_column.controls.append(ft.Text("Your cart is empty.", color=theme.MUTED))
        for c in cart:
            product = STORE.products.get(c["product_id"])
            if not product:
                continue
            items_column.controls.append(
                ft.Row([
                    ft.Icon(ft.Icons.CHECKROOM, color=theme.PRIMARY),
                    ft.Column([
                        ft.Text(product.name, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Size {c['size']}  •  Qty {c['quantity']}  •  ${product.price:.2f} each", size=12, color=theme.MUTED),
                    ], expand=True),
                    ft.Text(f"${product.price * c['quantity']:.2f}", weight=ft.FontWeight.BOLD),
                    ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color=theme.DANGER,
                                  on_click=lambda e, pid=c["product_id"], sz=c["size"]: remove_click(pid, sz)),
                ])
            )

        order_items = cart_order_items(page)
        summary_column.controls.clear()
        if order_items:
            breakdown = compute_cost_breakdown(order_items)
            summary_column.controls.extend([
                _row("Subtotal", breakdown.subtotal),
                _row("Payment processing fee", breakdown.payment_processing_fee),
                _row("Shipping (consolidated intl.)", breakdown.shipping_fee),
                ft.Divider(),
                _row("Total due at checkout", breakdown.total, bold=True),
                ft.Text(f"(Platform commission of ${breakdown.commission_fee:.2f} is deducted from the "
                        f"vendor's payout, not added to your total.)", size=11, color=theme.MUTED),
            ])
        else:
            summary_column.controls.append(ft.Text("Add items to see a cost breakdown.", size=12, color=theme.MUTED))
        page.update()

    def remove_click(pid, size):
        remove_from_cart(page, pid, size)
        render()

    def _row(label, value, bold=False):
        return ft.Row([
            ft.Text(label, weight=ft.FontWeight.BOLD if bold else None),
            ft.Text(f"${value:.2f}", weight=ft.FontWeight.BOLD if bold else None),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    render()

    return ft.View(
        route="/cart",
        appbar=theme.app_bar(page, "Your Cart", session),
        bgcolor=theme.LIGHT_BG,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                padding=24,
                content=ft.ResponsiveRow([
                    ft.Container(col={"sm": 12, "md": 7}, content=theme.section_card(
                        theme.heading("Items", size=18), items_column,
                    )),
                    ft.Container(col={"sm": 12, "md": 5}, content=theme.section_card(
                        theme.heading("Order summary", size=18),
                        summary_column,
                        theme.primary_button("Proceed to checkout", icon=ft.Icons.ARROW_FORWARD,
                                              on_click=lambda e: page.go("/checkout"), width=300),
                    )),
                ]),
            )
        ],
    )
