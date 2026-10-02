"""
ui/state.py
-------------
Small helpers for reading/writing per-browser-tab state that Flet
keeps in `page.session` (in-memory per connection, not shared between
users - each visitor gets their own session/cart, which is what a
real multi-user storefront needs).
"""

from __future__ import annotations

import flet as ft

from core.security import get_session, Session
from core.data_store import STORE, OrderItem


def current_session(page: ft.Page) -> Session | None:
    token = page.session.get("session_token")
    if not token:
        return None
    return get_session(token)


def require_login(page: ft.Page) -> Session | None:
    session = current_session(page)
    if session is None:
        page.go("/login")
        return None
    return session


def get_cart(page: ft.Page) -> list[dict]:
    """Cart is a list of dicts: {product_id, size, quantity} kept in
    page.session so each browser tab/user has an independent cart."""
    cart = page.session.get("cart")
    if cart is None:
        cart = []
        page.session.set("cart", cart)
    return cart


def add_to_cart(page: ft.Page, product_id: str, size: str, quantity: int = 1) -> None:
    cart = get_cart(page)
    for item in cart:
        if item["product_id"] == product_id and item["size"] == size:
            item["quantity"] += quantity
            page.session.set("cart", cart)
            return
    cart.append({"product_id": product_id, "size": size, "quantity": quantity})
    page.session.set("cart", cart)


def remove_from_cart(page: ft.Page, product_id: str, size: str) -> None:
    cart = [c for c in get_cart(page) if not (c["product_id"] == product_id and c["size"] == size)]
    page.session.set("cart", cart)


def clear_cart(page: ft.Page) -> None:
    page.session.set("cart", [])


def cart_order_items(page: ft.Page) -> list[OrderItem]:
    items = []
    for c in get_cart(page):
        product = STORE.products.get(c["product_id"])
        if product:
            items.append(OrderItem(
                product_id=product.id,
                name=product.name,
                unit_price=product.price,
                quantity=c["quantity"],
                size=c["size"],
            ))
    return items


def mark_walkthrough_seen(page: ft.Page) -> None:
    page.session.set("walkthrough_seen", True)


def has_seen_walkthrough(page: ft.Page) -> bool:
    return bool(page.session.get("walkthrough_seen"))
