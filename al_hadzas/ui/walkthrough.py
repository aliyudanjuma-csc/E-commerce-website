"""
ui/walkthrough.py
--------------------
First-run onboarding walkthrough.

HCI LAW APPLIED: JAKOB'S LAW
------------------------------
"Users spend most of their time on other sites/apps. They prefer your
site to work the same way as all the other sites they already know."

Why Jakob's Law fits AL-HADZAS COLLECTIONS specifically: the single
biggest adoption risk identified in the Idea & Validation research was
BUYER TRUST in an unfamiliar, niche storefront for a high-consideration
purchase (custom-fitted clothing, prepayment, cross-border shipping).
The fastest way to earn that trust is to make the shopping mechanics
feel exactly like a mainstream store the buyer already trusts (ASOS,
Amazon, Shein) - familiar cart icon top-right, familiar
browse -> filter -> product page -> size guide -> cart -> checkout
flow, familiar order-status stepper - and reserve novelty for the one
place it adds value: the cultural "Culture Notes" content, not the
navigation mechanics. This walkthrough exists specifically to tell the
first-time user "this will feel like stores you already know," which
directly operationalises Jakob's Law as an onboarding strategy.

Implementation note: step state is a simple closured index (not
page.session) since the walkthrough is inherently a single, disposable
view-local sequence.
"""

import flet as ft
from ui import theme
from ui.state import mark_walkthrough_seen

STEPS = [
    {
        "icon": ft.Icons.PUBLIC,
        "title": "Welcome to AL-HADZAS COLLECTIONS",
        "body": "Authentic traditional African attire, made by verified tailors and "
                "designers, shipped worldwide.",
    },
    {
        "icon": ft.Icons.SEARCH,
        "title": "Shop the way you already know how",
        "body": "Browse, search, filter by country/fabric/occasion, and check out - "
                "just like any store you already use. We kept the mechanics familiar "
                "on purpose, so you can focus on discovering pieces you love.",
    },
    {
        "icon": ft.Icons.STRAIGHTEN,
        "title": "Shop with confidence",
        "body": "Every product has a standardized sizing guide and 'Culture Notes' "
                "explaining its origin and meaning - so you always know what you're "
                "buying and from where.",
    },
    {
        "icon": ft.Icons.VERIFIED_USER,
        "title": "Verified vendors, protected payments",
        "body": "Every tailor/designer is reviewed before they can sell. Your payment "
                "is only released to the vendor once your order ships.",
    },
]


def walkthrough_view(page: ft.Page) -> ft.View:
    index = {"i": 0}
    body_container = ft.Container()

    def render():
        step = STEPS[index["i"]]
        is_last = index["i"] == len(STEPS) - 1
        body_container.content = ft.Column(
            [
                ft.Icon(step["icon"], size=72, color=theme.PRIMARY),
                ft.Container(height=16),
                theme.heading(step["title"], size=22),
                ft.Container(height=8),
                ft.Text(step["body"], size=14, color=theme.MUTED, text_align=ft.TextAlign.CENTER),
                ft.Container(height=24),
                ft.Row(
                    [ft.Container(
                        width=10, height=10, border_radius=5,
                        bgcolor=theme.PRIMARY if i == index["i"] else "#E0E0E0",
                    ) for i in range(len(STEPS))],
                    alignment=ft.MainAxisAlignment.CENTER, spacing=6,
                ),
                ft.Container(height=24),
                ft.Row(
                    [
                        ft.TextButton("Skip", on_click=lambda e: finish()),
                        theme.primary_button(
                            "Get started" if is_last else "Next",
                            on_click=lambda e: (finish() if is_last else next_step()),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        page.update()

    def next_step():
        index["i"] = min(index["i"] + 1, len(STEPS) - 1)
        render()

    def finish():
        mark_walkthrough_seen(page)
        page.go("/login")

    render()

    return ft.View(
        route="/walkthrough",
        bgcolor=theme.LIGHT_BG,
        controls=[
            ft.Container(
                content=ft.Container(
                    content=body_container,
                    width=420,
                    padding=32,
                    bgcolor="white",
                    border_radius=16,
                ),
                alignment=ft.alignment.center,
                expand=True,
            )
        ],
    )
