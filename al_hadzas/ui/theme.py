"""
ui/theme.py
------------
Central color palette and small reusable UI helpers, so every view
looks consistent. Colors are inspired by common West African textile
palettes (kente gold/terracotta/forest green) without reproducing any
specific copyrighted textile artwork.
"""

import flet as ft

PRIMARY = "#B5651D"      # terracotta
SECONDARY = "#2E7D32"    # forest green
ACCENT = "#D4AF37"       # kente gold
DARK = "#1B1B1B"
LIGHT_BG = "#FFF8F0"
DANGER = "#C62828"
MUTED = "#6B6B6B"


def heading(text: str, size: int = 24) -> ft.Text:
    return ft.Text(text, size=size, weight=ft.FontWeight.BOLD, color=DARK)


def subheading(text: str) -> ft.Text:
    return ft.Text(text, size=14, color=MUTED)


def primary_button(text: str, on_click=None, icon=None, width=None) -> ft.ElevatedButton:
    return ft.ElevatedButton(
        text=text,
        icon=icon,
        on_click=on_click,
        width=width,
        style=ft.ButtonStyle(
            bgcolor={ft.ControlState.DEFAULT: PRIMARY},
            color={ft.ControlState.DEFAULT: "white"},
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
    )


def section_card(*controls: ft.Control, padding=16) -> ft.Card:
    return ft.Card(
        content=ft.Container(
            content=ft.Column(controls, spacing=10),
            padding=padding,
        ),
        elevation=2,
    )


def app_bar(page: ft.Page, title: str, session) -> ft.AppBar:
    actions = []
    if session:
        actions.append(
            ft.IconButton(icon=ft.Icons.CHAT_BUBBLE_OUTLINE, tooltip="CRM Chat",
                           on_click=lambda e: page.go("/chat"))
        )
        actions.append(
            ft.IconButton(icon=ft.Icons.SHOPPING_CART_OUTLINED, tooltip="Cart",
                           on_click=lambda e: page.go("/cart"))
        )
        actions.append(
            ft.IconButton(icon=ft.Icons.LOGOUT, tooltip="Log out",
                           on_click=lambda e: _logout(page))
        )
    return ft.AppBar(
        title=ft.Text(title),
        bgcolor=PRIMARY,
        color="white",
        actions=actions,
    )


def _logout(page: ft.Page):
    from core.security import invalidate_session
    token = page.session.get("session_token")
    if token:
        invalidate_session(token)
    page.session.remove("session_token")
    page.session.remove("cart")
    page.go("/login")
