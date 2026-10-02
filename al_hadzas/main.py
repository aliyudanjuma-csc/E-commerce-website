"""
main.py
---------
AL-HADZAS COLLECTIONS - coursework e-commerce MVP entry point.

Run:
    pip install -r requirements.txt
    flet run --web main.py

Then open the URL Flet prints (typically http://localhost:8550).

Demo logins are printed to the console on startup (see core/seed_data.py).
"""

import flet as ft

from core.seed_data import seed
from ui.walkthrough import walkthrough_view
from ui.auth_view import login_view, register_view
from ui.home_view import home_view
from ui.product_view import product_view
from ui.cart_view import cart_view
from ui.checkout_view import checkout_view
from ui.orders_view import orders_view
from ui.vendor_dashboard import vendor_dashboard
from ui.admin_dashboard import admin_dashboard
from ui.chatbot_view import chatbot_view
from ui.legal_view import legal_view
from ui.state import has_seen_walkthrough


def main(page: ft.Page):
    page.title = "AL-HADZAS COLLECTIONS"
    page.window.width = 1200
    page.window.height = 800
    page.theme = ft.Theme(color_scheme_seed="#B5651D")
    page.padding = 0

    def route_change(e: ft.RouteChangeEvent):
        page.views.clear()
        route = page.route

        if route == "/" or route == "":
            target = "/login" if has_seen_walkthrough(page) else "/walkthrough"
            page.views.append(login_view(page) if target == "/login" else walkthrough_view(page))
        elif route == "/walkthrough":
            page.views.append(walkthrough_view(page))
        elif route == "/login":
            page.views.append(login_view(page))
        elif route == "/register":
            page.views.append(register_view(page))
        elif route == "/home":
            page.views.append(home_view(page))
        elif route.startswith("/product/"):
            product_id = route.split("/product/")[1]
            page.views.append(product_view(page, product_id))
        elif route == "/cart":
            page.views.append(cart_view(page))
        elif route == "/checkout":
            page.views.append(checkout_view(page))
        elif route == "/orders":
            page.views.append(orders_view(page))
        elif route == "/vendor":
            page.views.append(vendor_dashboard(page))
        elif route == "/admin":
            page.views.append(admin_dashboard(page))
        elif route == "/chat":
            page.views.append(chatbot_view(page))
        elif route.startswith("/legal/"):
            doc_key = route.split("/legal/")[1]
            page.views.append(legal_view(page, doc_key))
        else:
            page.views.append(login_view(page))

        page.update()

    def view_pop(e: ft.ViewPopEvent):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route or "/")


if __name__ == "__main__":
    seed()
    ft.app(target=main)
