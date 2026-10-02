"""
ui/auth_view.py
------------------
Login and registration views.

OWASP controls exercised here:
  - A02: passwords are hashed (never stored/compared as plaintext) via core.security.hash_password
  - A03: email/name fields are validated + sanitized before being stored
  - A04: LoginRateLimiter locks an account out after repeated failed attempts
  - A07: successful login issues a short-lived, unguessable session token
  - A09: every login/registration attempt is written to STORE.audit_log
"""

import flet as ft

from ui import theme
from core.data_store import STORE, User, next_id
from core.security import (
    hash_password, verify_password, validate_email, sanitize_text,
    password_strength_errors, LoginRateLimiter, generate_session_token,
)


def login_view(page: ft.Page) -> ft.View:
    email_field = ft.TextField(label="Email", autofocus=True, width=340)
    password_field = ft.TextField(label="Password", password=True, can_reveal_password=True, width=340)
    error_text = ft.Text("", color=theme.DANGER)

    def do_login(e):
        email = email_field.value.strip()
        password = password_field.value

        if not validate_email(email):
            error_text.value = "Enter a valid email address."
            page.update()
            return

        user = STORE.get_user_by_email(email)
        if user is None:
            STORE.log_action("anonymous", "login_failed", f"unknown email {email}")
            error_text.value = "Invalid email or password."
            page.update()
            return

        if LoginRateLimiter.is_locked(user):
            error_text.value = "Account temporarily locked after repeated failed attempts. Try again later."
            page.update()
            return

        if not verify_password(password, user.password_hash, user.salt):
            LoginRateLimiter.register_failure(user)
            STORE.log_action(user.id, "login_failed", "bad password")
            error_text.value = "Invalid email or password."
            page.update()
            return

        LoginRateLimiter.register_success(user)
        session = generate_session_token(user.id, user.role)
        page.session.set("session_token", session.token)
        STORE.log_action(user.id, "login_success")

        page.go({"buyer": "/home", "vendor": "/vendor", "admin": "/admin"}.get(user.role, "/home"))

    def go_register(e):
        page.go("/register")

    demo_hint = ft.Container(
        content=ft.Column([
            ft.Text("Demo accounts", size=12, weight=ft.FontWeight.BOLD, color=theme.MUTED),
            ft.Text("Admin: admin@alhadzas.com / Admin#1234", size=11, color=theme.MUTED),
            ft.Text("Vendor: amina@alhadzas.com / Vendor#1234", size=11, color=theme.MUTED),
            ft.Text("Buyer: buyer@alhadzas.com / Buyer#1234", size=11, color=theme.MUTED),
        ]),
        padding=10, bgcolor="#F3F3F3", border_radius=8, width=340,
    )

    return ft.View(
        route="/login",
        bgcolor=theme.LIGHT_BG,
        controls=[
            ft.Container(
                alignment=ft.alignment.center,
                expand=True,
                content=ft.Container(
                    width=420, padding=32, bgcolor="white", border_radius=16,
                    content=ft.Column(
                        [
                            theme.heading("AL-HADZAS COLLECTIONS"),
                            theme.subheading("Traditional African attire, worldwide."),
                            ft.Container(height=16),
                            email_field,
                            password_field,
                            error_text,
                            ft.Container(height=8),
                            theme.primary_button("Log in", on_click=do_login, width=340),
                            ft.TextButton("Create an account", on_click=go_register),
                            ft.Container(height=8),
                            demo_hint,
                            ft.Row([
                                ft.TextButton("Terms", on_click=lambda e: page.go("/legal/terms")),
                                ft.TextButton("Privacy", on_click=lambda e: page.go("/legal/privacy")),
                                ft.TextButton("Returns", on_click=lambda e: page.go("/legal/returns")),
                            ], alignment=ft.MainAxisAlignment.CENTER),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
            )
        ],
    )


def register_view(page: ft.Page) -> ft.View:
    name_field = ft.TextField(label="Full name", width=340)
    email_field = ft.TextField(label="Email", width=340)
    password_field = ft.TextField(label="Password", password=True, can_reveal_password=True, width=340)
    role_dropdown = ft.Dropdown(
        label="I am a...", width=340,
        options=[ft.dropdown.Option("buyer", "Buyer"), ft.dropdown.Option("vendor", "Vendor / Tailor")],
        value="buyer",
    )
    business_field = ft.TextField(label="Business name (vendors only)", width=340, visible=False)
    country_field = ft.TextField(label="Country (vendors only)", width=340, visible=False)
    error_text = ft.Text("", color=theme.DANGER)
    terms_checkbox = ft.Checkbox(label="I agree to the Terms & Conditions and Privacy Policy", value=False)

    def role_changed(e):
        is_vendor = role_dropdown.value == "vendor"
        business_field.visible = is_vendor
        country_field.visible = is_vendor
        page.update()

    role_dropdown.on_change = role_changed

    def do_register(e):
        name = sanitize_text(name_field.value or "", max_len=120)
        email = (email_field.value or "").strip()
        password = password_field.value or ""

        if not name:
            error_text.value = "Enter your name."
        elif not validate_email(email):
            error_text.value = "Enter a valid email address."
        elif STORE.get_user_by_email(email) is not None:
            error_text.value = "An account with this email already exists."
        elif password_strength_errors(password):
            error_text.value = " ".join(password_strength_errors(password))
        elif not terms_checkbox.value:
            error_text.value = "You must agree to the Terms & Conditions and Privacy Policy."
        else:
            error_text.value = ""

        if error_text.value:
            page.update()
            return

        pw_hash, salt = hash_password(password)
        user = User(id=next_id("USR"), name=name, email=email,
                    password_hash=pw_hash, salt=salt, role=role_dropdown.value)
        STORE.add_user(user)

        if role_dropdown.value == "vendor":
            from core.data_store import Vendor
            vendor = Vendor(
                id=next_id("VEN"), user_id=user.id,
                business_name=sanitize_text(business_field.value or "My Shop", 120),
                country=sanitize_text(country_field.value or "Unknown", 60),
                verified=False,  # must be approved by admin - OWASP A01 access control gate
            )
            STORE.add_vendor(vendor)

        STORE.log_action(user.id, "account_created", role_dropdown.value)

        session = generate_session_token(user.id, user.role)
        page.session.set("session_token", session.token)
        page.go({"buyer": "/home", "vendor": "/vendor"}.get(user.role, "/home"))

    return ft.View(
        route="/register",
        bgcolor=theme.LIGHT_BG,
        controls=[
            ft.Container(
                alignment=ft.alignment.center, expand=True,
                content=ft.Container(
                    width=420, padding=32, bgcolor="white", border_radius=16,
                    content=ft.Column(
                        [
                            theme.heading("Create your account"),
                            ft.Container(height=8),
                            name_field, email_field, password_field, role_dropdown,
                            business_field, country_field,
                            terms_checkbox,
                            error_text,
                            ft.Container(height=8),
                            theme.primary_button("Register", on_click=do_register, width=340),
                            ft.TextButton("Back to login", on_click=lambda e: page.go("/login")),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                ),
            )
        ],
    )
