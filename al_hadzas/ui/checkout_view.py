"""
ui/checkout_view.py
----------------------
Checkout: collects a simulated card payment (core.payment.process_payment,
fully offline/sandbox) and creates one Order per vendor represented in
the cart (a real marketplace settles/ships per-vendor independently),
each carrying its own itemized cost breakdown (micro components:
subtotal, commission, payment-processing fee, shipping).
"""

from collections import defaultdict

import flet as ft

from ui import theme
from ui.state import require_login, get_cart, cart_order_items, clear_cart
from core.data_store import STORE, Order, next_id
from core.payment import compute_cost_breakdown, process_payment


def checkout_view(page: ft.Page) -> ft.View:
    session = require_login(page)
    if session is None:
        return ft.View(route="/checkout", controls=[ft.ProgressRing()])

    order_items = cart_order_items(page)
    if not order_items:
        return ft.View(
            route="/checkout",
            appbar=theme.app_bar(page, "Checkout", session),
            controls=[ft.Container(padding=24, content=ft.Column([
                ft.Text("Your cart is empty."),
                theme.primary_button("Back to shop", on_click=lambda e: page.go("/home")),
            ]))],
        )

    # Group items by vendor so each vendor gets its own order + its own
    # cost breakdown (O(m) over m cart items, m is small).
    by_vendor = defaultdict(list)
    for item in order_items:
        product = STORE.products.get(item.product_id)
        if product:
            by_vendor[product.vendor_id].append(item)

    grand_total = sum(compute_cost_breakdown(items).total for items in by_vendor.values())

    card_field = ft.TextField(label="Card number", hint_text="4242 4242 4242 4242", width=320)
    expiry_field = ft.TextField(label="Expiry (MM/YY)", hint_text="12/29", width=150)
    cvc_field = ft.TextField(label="CVC", hint_text="123", width=100, password=True)
    error_text = ft.Text("", color=theme.DANGER)
    result_container = ft.Container()

    breakdown_rows = []
    for vendor_id, items in by_vendor.items():
        vendor = STORE.vendors.get(vendor_id)
        b = compute_cost_breakdown(items)
        breakdown_rows.append(ft.Column([
            ft.Text(vendor.business_name if vendor else "Vendor", weight=ft.FontWeight.BOLD),
            *[ft.Text(f"  {i.quantity} x {i.name} ({i.size}) - ${i.unit_price*i.quantity:.2f}", size=12) for i in items],
            ft.Text(f"  Subtotal ${b.subtotal:.2f} + processing ${b.payment_processing_fee:.2f} + shipping ${b.shipping_fee:.2f} = ${b.total:.2f}",
                    size=12, color=theme.MUTED),
        ], spacing=2))

    def pay_click(e):
        result = process_payment(card_field.value or "", expiry_field.value or "", cvc_field.value or "", grand_total)
        if not result.success:
            error_text.value = result.message
            page.update()
            return

        created_orders = []
        for vendor_id, items in by_vendor.items():
            b = compute_cost_breakdown(items)
            order = Order(
                id=next_id("ORD"),
                buyer_id=session.user_id,
                vendor_id=vendor_id,
                items=items,
                subtotal=b.subtotal,
                commission_fee=b.commission_fee,
                payment_processing_fee=b.payment_processing_fee,
                shipping_fee=b.shipping_fee,
                total=b.total,
            )
            order.history.append(("placed", order.created_at))
            STORE.add_order(order)
            created_orders.append(order)

        STORE.log_action(session.user_id, "checkout_success",
                          f"ref={result.reference} orders={[o.id for o in created_orders]}")
        clear_cart(page)

        result_container.content = ft.Column([
            ft.Icon(ft.Icons.CHECK_CIRCLE, color=theme.SECONDARY, size=48),
            theme.heading("Payment successful!"),
            ft.Text(f"Reference: {result.reference}"),
            ft.Text("Order id(s): " + ", ".join(o.id for o in created_orders)),
            theme.primary_button("View my orders", on_click=lambda e: page.go("/orders")),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        page.update()

    pay_form = ft.Column([
        theme.heading("Payment details (simulated sandbox)", size=16),
        ft.Text("No real card is charged. This models a Stripe/Paystack-style flow for the coursework demo.",
                size=11, color=theme.MUTED),
        card_field, ft.Row([expiry_field, cvc_field]),
        error_text,
        theme.primary_button("Pay now", icon=ft.Icons.LOCK, on_click=pay_click, width=320),
    ], spacing=10)

    return ft.View(
        route="/checkout",
        appbar=theme.app_bar(page, "Checkout", session),
        bgcolor=theme.LIGHT_BG,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                padding=24,
                content=ft.ResponsiveRow([
                    ft.Container(col={"sm": 12, "md": 6}, content=theme.section_card(
                        theme.heading("Order breakdown", size=18),
                        ft.Column(breakdown_rows, spacing=12),
                        ft.Divider(),
                        ft.Row([ft.Text("Grand total", weight=ft.FontWeight.BOLD, size=16),
                                ft.Text(f"${grand_total:.2f}", weight=ft.FontWeight.BOLD, size=16)],
                               alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    )),
                    ft.Container(col={"sm": 12, "md": 6}, content=theme.section_card(pay_form)),
                ]),
                bgcolor=theme.LIGHT_BG,
            ),
            result_container,
        ],
    )
