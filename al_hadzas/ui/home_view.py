"""
ui/home_view.py
------------------
Buyer-facing catalogue: semantic search bar (RAG-style retrieval via
core.search.SemanticSearchIndex) plus simple filters, rendered as a
responsive grid of product cards.

The search index is rebuilt (O(n)) once per view load from the current
catalogue, then each keystroke-triggered query is O(n) to score +
O(n log k) to rank (see core/search.py for the full complexity note).
"""

import flet as ft

from ui import theme
from ui.state import require_login, add_to_cart
from core.data_store import STORE
from core.search import SemanticSearchIndex


def home_view(page: ft.Page) -> ft.View:
    session = require_login(page)
    if session is None:
        return ft.View(route="/home", controls=[ft.ProgressRing()])

    index = SemanticSearchIndex()
    index.build(STORE.all_products())  # O(n)

    grid = ft.GridView(expand=True, runs_count=0, max_extent=260, spacing=14, run_spacing=14)

    def product_card(product) -> ft.Card:
        rating, count = STORE.product_rating(product.id)
        return ft.Card(
            content=ft.Container(
                padding=14,
                content=ft.Column(
                    [
                        ft.Container(
                            content=ft.Icon(ft.Icons.CHECKROOM, size=48, color=theme.PRIMARY),
                            alignment=ft.alignment.center, height=90,
                            bgcolor="#F3E9DC", border_radius=8,
                        ),
                        ft.Text(product.name, weight=ft.FontWeight.BOLD, max_lines=2),
                        ft.Text(f"{product.country_of_origin} - {product.fabric}", size=11, color=theme.MUTED, max_lines=1),
                        ft.Row([
                            ft.Text(f"${product.price:.2f}", weight=ft.FontWeight.BOLD, color=theme.PRIMARY),
                            ft.Row([ft.Icon(ft.Icons.STAR, size=14, color=theme.ACCENT),
                                    ft.Text(f"{rating} ({count})", size=11, color=theme.MUTED)], spacing=2),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.ElevatedButton(
                            "View", width=200,
                            on_click=lambda e, pid=product.id: page.go(f"/product/{pid}"),
                        ),
                    ],
                    spacing=6,
                ),
            ),
        )

    def render_products(products):
        grid.controls = [product_card(p) for p in products]
        page.update()

    def do_search(e=None):
        query = search_field.value or ""
        if not query.strip():
            render_products(STORE.all_products())
            result_label.value = f"Showing all {len(STORE.products)} products"
        else:
            hits = index.search(query, top_k=12)
            render_products([h.product for h in hits])
            result_label.value = f"{len(hits)} result(s) for \"{query}\" (semantic search)"
        page.update()

    search_field = ft.TextField(
        hint_text="Try: 'wedding Agbada', 'Kente dress Ghana', 'everyday cotton'...",
        expand=True, on_submit=do_search, prefix_icon=ft.Icons.SEARCH,
    )
    result_label = ft.Text(f"Showing all {len(STORE.products)} products", size=12, color=theme.MUTED)

    def country_filter_changed(e):
        val = country_filter.value
        products = STORE.all_products() if val == "All" else [p for p in STORE.all_products() if p.country_of_origin == val]
        render_products(products)
        result_label.value = f"Showing {len(products)} product(s) from {val}"
        page.update()

    countries = sorted({p.country_of_origin for p in STORE.all_products()})
    country_filter = ft.Dropdown(
        label="Country", width=180,
        options=[ft.dropdown.Option("All")] + [ft.dropdown.Option(c) for c in countries],
        value="All", on_change=country_filter_changed,
    )

    render_products(STORE.all_products())

    return ft.View(
        route="/home",
        appbar=theme.app_bar(page, "AL-HADZAS COLLECTIONS", session),
        bgcolor=theme.LIGHT_BG,
        padding=0,
        controls=[
            ft.Container(
                padding=20,
                expand=True,
                content=ft.Column(
                    [
                        ft.Row([search_field, country_filter, ft.IconButton(icon=ft.Icons.SEARCH, on_click=do_search)]),
                        result_label,
                        ft.Container(height=8),
                        grid,
                    ],
                    expand=True,
                ),
            )
        ],
    )
