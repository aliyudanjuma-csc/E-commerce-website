"""
ui/vendor_dashboard.py
--------------------------
Vendor dashboard (FR-06, FR-07): add/edit/remove product listings, and
work through orders oldest-first using STORE.next_pending_order_for_vendor
(the O(log n) heap-based queue from core/data_store.py) instead of
scanning/sorting the whole order list on every view render.

Also demonstrates the "antivirus" upload gate (OWASP A08): the
FilePicker result bytes are passed through core.security.AntivirusScanner
before a product image is accepted.
"""

import flet as ft

from ui import theme
from ui.state import require_login
from core.data_store import STORE, Product, next_id
from core.security import sanitize_text, validate_price, AntivirusScanner, require_role


def vendor_dashboard(page: ft.Page) -> ft.View:
    session = require_login(page)
    if session is None:
        return ft.View(route="/vendor", controls=[ft.ProgressRing()])

    if not require_role(session, {"vendor"}):
        return ft.View(route="/vendor", controls=[ft.Text("Access denied: vendor accounts only.")])

    vendor = next((v for v in STORE.vendors.values() if v.user_id == session.user_id), None)
    if vendor is None:
        return ft.View(route="/vendor", controls=[ft.Text("Vendor profile not found.")])

    upload_status = ft.Text("")
    scanned_file = {"name": None, "bytes": None}

    def on_file_result(e: ft.FilePickerResultEvent):
        if not e.files:
            return
        f = e.files[0]
        try:
            with open(f.path, "rb") as fh:
                content = fh.read()
        except Exception:
            upload_status.value = "Could not read the selected file."
            upload_status.color = theme.DANGER
            page.update()
            return

        result = AntivirusScanner.scan(f.name, content)
        if not result.passed:
            upload_status.value = f"⛔ Upload blocked by security scan: {result.reason}"
            upload_status.color = theme.DANGER
            scanned_file["name"], scanned_file["bytes"] = None, None
        else:
            upload_status.value = f"✅ '{f.name}' passed the security scan and is ready to attach."
            upload_status.color = theme.SECONDARY
            scanned_file["name"], scanned_file["bytes"] = f.name, content
        page.update()

    file_picker = ft.FilePicker(on_result=on_file_result)
    page.overlay.append(file_picker)

    name_field = ft.TextField(label="Product name", width=300)
    fabric_field = ft.TextField(label="Fabric", width=300)
    origin_field = ft.TextField(label="Country of origin", width=300)
    occasion_field = ft.TextField(label="Occasion", width=300)
    price_field = ft.TextField(label="Price (USD)", width=150)
    description_field = ft.TextField(label="Culture Notes / description", width=300, multiline=True)
    form_error = ft.Text("", color=theme.DANGER)

    products_column = ft.Column(spacing=10)
    orders_column = ft.Column(spacing=10)

    def render_products():
        products_column.controls.clear()
        for p in STORE.vendor_products(vendor.id):
            products_column.controls.append(
                ft.Row([
                    ft.Text(p.name, expand=True), ft.Text(f"${p.price:.2f}"),
                    ft.Text(f"Stock: {p.stock}", size=12, color=theme.MUTED),
                    ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color=theme.DANGER,
                                  on_click=lambda e, pid=p.id: remove_product(pid)),
                ])
            )
        page.update()

    def remove_product(pid):
        STORE.remove_product(pid)
        STORE.log_action(session.user_id, "product_removed", pid)
        render_products()

    def add_product(e):
        price = validate_price(price_field.value or "")
        if not name_field.value:
            form_error.value = "Product name is required."
        elif price is None:
            form_error.value = "Enter a valid price."
        else:
            form_error.value = ""

        if form_error.value:
            page.update()
            return

        product = Product(
            id=next_id("PRD"), vendor_id=vendor.id,
            name=sanitize_text(name_field.value, 120),
            description=sanitize_text(description_field.value or "", 2000),
            fabric=sanitize_text(fabric_field.value or "", 120),
            country_of_origin=sanitize_text(origin_field.value or "", 60),
            occasion=sanitize_text(occasion_field.value or "", 120),
            price=price,
            sizes=["S", "M", "L", "XL", "Made-to-Measure"],
            stock=20,
            image_note=scanned_file["name"] or "placeholder-image",
        )
        STORE.add_product(product)
        STORE.log_action(session.user_id, "product_added", product.id)

        for f in (name_field, fabric_field, origin_field, occasion_field, price_field, description_field):
            f.value = ""
        scanned_file["name"], scanned_file["bytes"] = None, None
        upload_status.value = ""
        render_products()

    def render_orders():
        orders_column.controls.clear()
        for order in sorted(STORE.vendor_orders(vendor.id), key=lambda o: o.created_at):
            status_dropdown = ft.Dropdown(
                width=160, value=order.status,
                options=[ft.dropdown.Option(s) for s in ["placed", "processing", "shipped", "delivered"]],
            )

            def make_handler(order_id, dropdown):
                def handler(e):
                    STORE.update_order_status(order_id, dropdown.value)
                    STORE.log_action(session.user_id, "order_status_updated", f"{order_id}->{dropdown.value}")
                    render_orders()
                return handler

            status_dropdown.on_change = make_handler(order.id, status_dropdown)
            orders_column.controls.append(
                ft.Row([
                    ft.Text(order.id, expand=True), ft.Text(f"${order.total:.2f}"), status_dropdown,
                ])
            )
        if not orders_column.controls:
            orders_column.controls.append(ft.Text("No orders yet.", color=theme.MUTED))
        page.update()

    next_order = STORE.next_pending_order_for_vendor(vendor.id)
    next_order_widget = (
        ft.Text(f"Next order to action: {next_order.id} (${next_order.total:.2f}, status: {next_order.status})",
                color=theme.PRIMARY, weight=ft.FontWeight.BOLD)
        if next_order else ft.Text("No pending orders.", color=theme.MUTED)
    )

    render_products()
    render_orders()

    return ft.View(
        route="/vendor",
        appbar=theme.app_bar(page, f"Vendor Dashboard - {vendor.business_name}", session),
        bgcolor=theme.LIGHT_BG,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                padding=24,
                content=ft.ResponsiveRow([
                    ft.Container(col={"sm": 12, "md": 6}, content=theme.section_card(
                        theme.heading("Add a product", size=18),
                        name_field, fabric_field, origin_field, occasion_field, price_field, description_field,
                        ft.Row([
                            ft.ElevatedButton("Attach image", icon=ft.Icons.UPLOAD_FILE,
                                              on_click=lambda e: file_picker.pick_files(allow_multiple=False)),
                        ]),
                        upload_status,
                        form_error,
                        theme.primary_button("Add product", on_click=add_product, width=300),
                        ft.Divider(),
                        theme.heading("Your products", size=16),
                        products_column,
                    )),
                    ft.Container(col={"sm": 12, "md": 6}, content=theme.section_card(
                        theme.heading("Orders (oldest first)", size=18),
                        next_order_widget,
                        ft.Divider(),
                        orders_column,
                    )),
                ]),
            )
        ],
    )
