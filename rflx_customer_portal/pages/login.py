"""Login page — the login form + gating entry point."""

import reflex as rx

from rflx_customer_portal.states.auth_state import AuthState


@rx.page(route="/login")
def login() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading("Sign in", size="7"),
            rx.text(
                "Access your orders, tickets, and account details.",
                color=rx.color("slate", 10),
                size="3",
            ),
            rx.cond(
                AuthState.login_error != "",
                rx.callout(
                    AuthState.login_error,
                    icon="triangle-alert",
                    color_scheme="red",
                    width="100%",
                ),
            ),
            rx.vstack(
                rx.text("Username", size="2", weight="medium"),
                rx.input(
                    value=AuthState.login_username,
                    on_change=AuthState.set_login_username,
                    placeholder="username",
                    width="100%",
                ),
                rx.text("Password", size="2", weight="medium"),
                rx.input(
                    value=AuthState.login_password,
                    on_change=AuthState.set_login_password,
                    type="password",
                    placeholder="••••••••",
                    width="100%",
                ),
                spacing="2",
                width="100%",
            ),
            rx.button(
                "Sign in",
                on_click=AuthState.login,
                width="100%",
                size="3",
            ),
            spacing="4",
            width="24em",
            padding="2em",
            border=f"1px solid {rx.color('slate', 5)}",
            border_radius="0.75em",
        ),
        min_height="100vh",
        background=rx.color("slate", 2),
    )
