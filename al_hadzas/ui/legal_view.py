"""
ui/legal_view.py
-------------------
Renders the three required legal/policy pages from core/legal_content.py.
Accessible pre-login (from the login screen) and from within the app.
"""

import flet as ft

from ui import theme
from core.legal_content import TERMS_AND_CONDITIONS, PRIVACY_POLICY, RETURNS_POLICY

_DOCS = {
    "terms": ("Terms & Conditions", TERMS_AND_CONDITIONS),
    "privacy": ("Privacy Policy", PRIVACY_POLICY),
    "returns": ("Return & Refund Policy", RETURNS_POLICY),
}


def legal_view(page: ft.Page, doc_key: str) -> ft.View:
    title, body = _DOCS.get(doc_key, ("Not found", "This document does not exist."))

    from ui.state import current_session
    session = current_session(page)
    back_route = {"buyer": "/home", "vendor": "/vendor", "admin": "/admin"}.get(
        session.role if session else None, "/login")

    return ft.View(
        route=f"/legal/{doc_key}",
        appbar=ft.AppBar(
            title=ft.Text(title), bgcolor=theme.PRIMARY, color="white",
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: page.go(back_route)),
        ),
        bgcolor=theme.LIGHT_BG,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                padding=24,
                content=ft.Container(
                    width=800, bgcolor="white", padding=24, border_radius=12,
                    content=ft.Text(body, size=13, selectable=True),
                ),
                alignment=ft.alignment.top_center,
            )
        ],
    )
