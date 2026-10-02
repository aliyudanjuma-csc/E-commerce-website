"""
ui/product_view.py
---------------------
Product detail page: image placeholder, price, "Culture Notes"
(the product description used for semantic search - see core/search.py),
a standardized sizing guide, existing reviews, and add-to-cart.
"""

import flet as ft

from ui import theme
from ui.state import require_login, add_to_cart
from core.data_store import STORE

SIZE_GUIDE = {
    "S": "Bust 86-90cm / Waist 66-70cm",
    "M": "Bust 91-95cm / Waist 71-75cm",
    "L": "Bust 96-102cm / Waist 76-82cm",
    "XL": "Bust 103-110cm / Waist 83-90cm",
    "Made-to-Measure": "Enter your own measurements at checkout.",
}


def product_view(page: ft.Page, product_id: str) -> ft.View:
    session = require_login(page)
    if session is None:
        return ft.View(route=f"/product/{product_id}", controls=[ft.ProgressRing()])

    product = STORE.products.get(product_id)
    if product is None:
        return ft.View(
            route=f"/product/{product_id}",
            appbar=theme.app_bar(page, "Not found", session),
            controls=[ft.Text("Product not found.")],
        )

    vendor = STORE.vendors.get(product.vendor_id)
    rating, count = STORE.product_rating(product.id)
    reviews = STORE.reviews.get(product.id, [])

    size_dropdown = ft.Dropdown(
        label="Size", width=220,
        options=[ft.dropdown.Option(s) for s in product.sizes],
        value=product.sizes[0],
    )
    size_note = ft.Text(SIZE_GUIDE.get(product.sizes[0], ""), size=12, color=theme.MUTED)

    def size_changed(e):
        size_note.value = SIZE_GUIDE.get(size_dropdown.value, "")
        page.update()

    size_dropdown.on_change = size_changed

    qty_field = ft.TextField(label="Qty", value="1", width=80)
    snackbar_text = ft.Text("")

    def add_cart_click(e):
        try:
            qty = max(1, int(qty_field.value))
        except ValueError:
            qty = 1
        add_to_cart(page, product.id, size_dropdown.value, qty)
        page.open(ft.SnackBar(ft.Text(f"Added {qty} x {product.name} ({size_dropdown.value}) to cart.")))
        page.update()

    review_rows = [
        ft.Row([
            ft.Row([ft.Icon(ft.Icons.STAR, size=14, color=theme.ACCENT) for _ in range(r.rating)]),
            ft.Text(r.comment, size=12, expand=True),
        ])
        for r in reviews[-5:]
    ] or [ft.Text("No reviews yet - be the first to review after purchase.", size=12, color=theme.MUTED)]

    return ft.View(
        route=f"/product/{product_id}",
        appbar=theme.app_bar(page, product.name, session),
        bgcolor=theme.LIGHT_BG,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                padding=24,
                content=ft.ResponsiveRow([
                    ft.Container(
                        col={"sm": 12, "md": 5},
                        content=ft.Container(
                            content=ft.Icon(ft.Icons.CHECKROOM, size=120, color=theme.PRIMARY),
                            alignment=ft.alignment.center, height=320,
                            bgcolor="#F3E9DC", border_radius=12,
                        ),
                    ),
                    ft.Container(
                        col={"sm": 12, "md": 7},
                        content=ft.Column([
                            theme.heading(product.name, size=26),
                            ft.Row([
                                ft.Icon(ft.Icons.STAR, size=16, color=theme.ACCENT),
                                ft.Text(f"{rating} ({count} reviews)", size=13, color=theme.MUTED),
                                ft.Text("•", color=theme.MUTED),
                                ft.Text(f"Sold by {vendor.business_name if vendor else 'Unknown'}"
                                        + (" ✅ verified" if (vendor and vendor.verified) else ""),
                                        size=13, color=theme.MUTED),
                            ]),
                            ft.Text(f"${product.price:.2f}", size=24, weight=ft.FontWeight.BOLD, color=theme.PRIMARY),
                            ft.Divider(),
                            theme.heading("Culture Notes", size=16),
                            ft.Text(product.description, size=14),
                            ft.Text(f"Fabric: {product.fabric}  •  Origin: {product.country_of_origin}  •  Occasion: {product.occasion}",
                                    size=12, color=theme.MUTED),
                            ft.Divider(),
                            theme.heading("Sizing guide", size=16),
                            ft.Row([size_dropdown, qty_field]),
                            size_note,
                            ft.Container(height=8),
                            theme.primary_button("Add to cart", icon=ft.Icons.ADD_SHOPPING_CART, on_click=add_cart_click, width=260),
                            ft.Divider(),
                            theme.heading("Reviews", size=16),
                            ft.Column(review_rows, spacing=8),
                        ], spacing=8),
                    ),
                ]),
            )
        ],
    )
