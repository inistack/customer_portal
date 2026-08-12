"""Dashboard — the logged-in customer's own orders, and their tickets
(which they can create and update)."""

import reflex as rx

from rflx_customer_portal.components.navbar import navbar
from rflx_customer_portal.models import Order, Ticket
from rflx_customer_portal.states.auth_state import AuthState
from rflx_customer_portal.states.portal_state import PortalState


def _status_badge(status: str) -> rx.Component:
    scheme = rx.match(
        status,
        ("delivered", "resolved", "closed", "grass"),
        ("shipped", "processing", "pending", "blue"),
        ("open", "amber"),
        ("cancelled", "red"),
        "gray",
    )
    return rx.badge(status, color_scheme=scheme, variant="soft")


def _orders_table() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("Order"),
                rx.table.column_header_cell("Item"),
                rx.table.column_header_cell("Status"),
                rx.table.column_header_cell("Placed on"),
                rx.table.column_header_cell("Amount"),
            ),
        ),
        rx.table.body(
            rx.foreach(
                PortalState.my_orders,
                lambda order: rx.table.row(
                    rx.table.cell(order.order_id),
                    rx.table.cell(order.item),
                    rx.table.cell(_status_badge(order.status)),
                    rx.table.cell(order.placed_on),
                    rx.table.cell(order.amount_display),
                ),
            ),
        ),
        width="100%",
        variant="surface",
    )

def _tickets_table() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("Ticket"),
                rx.table.column_header_cell("Subject"),
                rx.table.column_header_cell("Status"),
                rx.table.column_header_cell("Priority"),
                rx.table.column_header_cell("Opened on"),
                rx.table.column_header_cell(""),
            ),
        ),
        rx.table.body(
            rx.foreach(
                PortalState.my_tickets,
                lambda ticket: rx.table.row(
                    rx.table.cell(ticket.ticket_id),
                    rx.table.cell(ticket.subject),
                    rx.table.cell(_status_badge(ticket.status)),
                    rx.table.cell(ticket.priority),
                    rx.table.cell(ticket.opened_on),
                    rx.table.cell(
                        rx.button(
                            "Edit",
                            size="1",
                            variant="soft",
                            color_scheme="gray",
                            on_click=lambda: PortalState.open_edit_ticket(
                                ticket.ticket_id
                            ),
                        ),
                    ),
                ),
            ),
        ),
        width="100%",
        variant="surface",
    )

def _ticket_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.cond(
                    PortalState.ticket_dialog_mode == "create",
                    "New ticket",
                    "Edit ticket",
                ),
            ),
            rx.cond(
                PortalState.ticket_form_error != "",
                rx.callout(
                    PortalState.ticket_form_error,
                    icon="triangle-alert",
                    color_scheme="red",
                    size="1",
                    margin_bottom="0.75em",
                ),
            ),
            rx.vstack(
                rx.text("Subject", size="2", weight="medium"),
                rx.input(
                    value=PortalState.ticket_form_subject,
                    on_change=PortalState.set_ticket_form_subject,
                    placeholder="What's the issue?",
                    width="100%",
                ),
                rx.text("Priority", size="2", weight="medium"),
                rx.select(
                    ["low", "medium", "high"],
                    value=PortalState.ticket_form_priority,
                    on_change=PortalState.set_ticket_form_priority,
                    width="100%",
                ),
                rx.cond(
                    PortalState.ticket_dialog_mode == "edit",
                    rx.fragment(
                        rx.text("Status", size="2", weight="medium"),
                        rx.select(
                            ["open", "pending", "resolved", "closed"],
                            value=PortalState.ticket_form_status,
                            on_change=PortalState.set_ticket_form_status,
                            width="100%",
                        ),
                    ),
                ),
                spacing="2",
                width="100%",
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button("Cancel", variant="soft", color_scheme="gray"),
                ),
                rx.button("Save", on_click=PortalState.save_ticket),
                spacing="3",
                justify="end",
                width="100%",
                margin_top="1.25em",
            ),
        ),
        open=PortalState.ticket_dialog_open,
        on_open_change=PortalState.set_ticket_dialog_open,
    )


@rx.page(route="/dashboard", on_load=AuthState.require_login)
def dashboard() -> rx.Component:
    return rx.box(
        navbar(),
        _ticket_dialog(),
        rx.container(
            rx.vstack(
                rx.heading(
                    f"Welcome back, {PortalState.customer_full_name}",
                    size="6",
                ),
                rx.text(
                    rx.cond(
                        PortalState.open_ticket_count > 0,
                        f"You have {PortalState.open_ticket_count} open or pending ticket(s).",
                        "No open tickets right now.",
                    ),
                    color=rx.color("slate", 10),
                ),
                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger("Orders", value="orders"),
                        rx.tabs.trigger("Tickets", value="tickets"),
                    ),
                    rx.tabs.content(
                        _orders_table(), value="orders", padding_top="1em"
                    ),
                    rx.tabs.content(
                        rx.vstack(
                            rx.hstack(
                                rx.spacer(),
                                rx.button(
                                    "New ticket",
                                    on_click=PortalState.open_create_ticket,
                                    size="2",
                                ),
                                width="100%",
                            ),
                            _tickets_table(),
                            spacing="3",
                            width="100%",
                        ),
                        value="tickets",
                        padding_top="1em",
                    ),
                    default_value="orders",
                    width="100%",
                ),
                spacing="4",
                width="100%",
                padding_y="2em",
            ),
        ),
    )
