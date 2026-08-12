"""Account / profile page — the logged-in customer can view and update
their own name, email, and company."""

import reflex as rx

from rflx_customer_portal.components.navbar import navbar
from rflx_customer_portal.states.portal_state import PortalState


@rx.page(route="/account", on_load=PortalState.on_account_load)
def account() -> rx.Component:
    return rx.box(
        navbar(),
        rx.container(
            rx.vstack(
                rx.heading("Account", size="6"),
                rx.text(
                    "Update your profile details below.",
                    color=rx.color("slate", 10),
                ),
                rx.cond(
                    PortalState.profile_form_error != "",
                    rx.callout(
                        PortalState.profile_form_error,
                        icon="triangle-alert",
                        color_scheme="red",
                        width="100%",
                        max_width="28em",
                    ),
                ),
                rx.cond(
                    PortalState.profile_save_message != "",
                    rx.callout(
                        PortalState.profile_save_message,
                        icon="check",
                        color_scheme="grass",
                        width="100%",
                        max_width="28em",
                    ),
                ),
                rx.vstack(
                    rx.text("Full name", size="2", weight="medium"),
                    rx.input(
                        value=PortalState.edit_full_name,
                        on_change=PortalState.set_edit_full_name,
                        width="100%",
                    ),
                    rx.text("Email", size="2", weight="medium"),
                    rx.input(
                        value=PortalState.edit_email,
                        on_change=PortalState.set_edit_email,
                        width="100%",
                    ),
                    rx.text("Company", size="2", weight="medium"),
                    rx.input(
                        value=PortalState.edit_company,
                        on_change=PortalState.set_edit_company,
                        width="100%",
                    ),
                    rx.hstack(
                        rx.text(
                            "Plan",
                            size="2",
                            color=rx.color("slate", 10),
                            width="9em",
                        ),
                        rx.badge(PortalState.customer_plan, variant="soft"),
                        align="center",
                        padding_top="0.4em",
                    ),
                    rx.text(
                        "Plan changes go through billing, not this form.",
                        size="1",
                        color=rx.color("slate", 9),
                    ),
                    rx.button(
                        "Save changes",
                        on_click=PortalState.save_profile,
                        margin_top="0.5em",
                    ),
                    spacing="3",
                    width="100%",
                    max_width="28em",
                    margin_top="0.5em",
                ),
                spacing="3",
                width="100%",
                padding_y="2em",
            ),
        ),
    )
