"""Shared navigation for every protected portal page."""

import reflex as rx

from rflx_customer_portal.states.auth_state import AuthState
from rflx_customer_portal.states.portal_state import PortalState


def nav_link(text: str, href: str) -> rx.Component:
    return rx.link(
        text,
        href=href,
        color=rx.color("slate", 11),
        weight="medium",
        _hover={"color": rx.color("slate", 12)},
    )


def navbar() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.hstack(
                rx.icon("layout-dashboard", size=20),
                rx.heading("Customer Portal", size="4"),
                spacing="2",
                align="center",
            ),
            rx.spacer(),
            rx.hstack(
                nav_link("Dashboard", "/dashboard"),
                nav_link("Account", "/account"),
                spacing="5",
                align="center",
            ),
            rx.spacer(),
            rx.hstack(
                rx.text(PortalState.customer_full_name, size="2", weight="medium"),
                rx.button(
                    "Log out",
                    on_click=AuthState.logout,
                    size="2",
                    variant="soft",
                    color_scheme="gray",
                ),
                spacing="3",
                align="center",
            ),
            width="100%",
            align="center",
            padding="1em 1.5em",
        ),
        border_bottom=f"1px solid {rx.color('slate', 5)}",
        width="100%",
        position="sticky",
        top="0",
        background=rx.color("slate", 1),
        z_index="10",
    )
