"""
ui/chatbot_view.py
---------------------
Chat-style UI for the CRM/support chatbot (core/chatbot.py). Keeps
message history in page.session so it persists across a browsing
session but never leaks between different users/tabs.
"""

import flet as ft

from ui import theme
from ui.state import require_login
from core.data_store import STORE
from core.search import SemanticSearchIndex
from core import chatbot as chatbot_engine


def chatbot_view(page: ft.Page) -> ft.View:
    session = require_login(page)
    if session is None:
        return ft.View(route="/chat", controls=[ft.ProgressRing()])

    history = page.session.get("chat_history")
    if history is None:
        history = [{"role": "bot", "text": "Hi! I'm the AL-HADZAS assistant. Ask me about sizing, "
                                             "an order id, shipping, returns, or search for a style."}]
        page.session.set("chat_history", history)

    product_index = SemanticSearchIndex()
    product_index.build(STORE.all_products())

    messages_column = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

    def bubble(role, text):
        is_bot = role == "bot"
        return ft.Row(
            [ft.Container(
                content=ft.Text(text, size=13, color="white" if not is_bot else theme.DARK, selectable=True),
                padding=10, border_radius=12,
                bgcolor=theme.PRIMARY if not is_bot else "#EFEFEF",
                width=380,
            )],
            alignment=ft.MainAxisAlignment.END if not is_bot else ft.MainAxisAlignment.START,
        )

    def render():
        messages_column.controls = [bubble(m["role"], m["text"]) for m in history]
        page.update()

    input_field = ft.TextField(hint_text="Ask about sizing, an order id, or search a style...", expand=True)

    def send(e=None):
        text = (input_field.value or "").strip()
        if not text:
            return
        history.append({"role": "user", "text": text})
        reply = chatbot_engine.answer(text, product_index, buyer_id=session.user_id)
        history.append({"role": "bot", "text": reply})
        page.session.set("chat_history", history)
        input_field.value = ""
        render()

    input_field.on_submit = send
    render()

    return ft.View(
        route="/chat",
        appbar=theme.app_bar(page, "AL-HADZAS Assistant", session),
        bgcolor=theme.LIGHT_BG,
        controls=[
            ft.Container(
                padding=20, expand=True,
                content=ft.Column([
                    ft.Container(content=messages_column, expand=True),
                    ft.Row([input_field, ft.IconButton(icon=ft.Icons.SEND, on_click=send)]),
                ], expand=True),
            )
        ],
    )
