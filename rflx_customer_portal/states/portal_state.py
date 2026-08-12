"""Per-customer portal data, scoped to whoever is currently logged in.

PortalState inherits AuthState because it needs `current_customer_id` —
per Reflex's state-structure docs, inheriting from a parent state is the
right call specifically when the parent holds data the substate commonly
depends on (rather than every substate hanging off the root State).

Every computed var below is a live lookup keyed by
`self.current_customer_id`, not a value baked in at compile time — this
is what makes the per-customer scoping actually real instead of cosmetic.

Note on `cache=False`: these computed vars read from SEEDED_TICKETS /
SEEDED_CUSTOMERS, which are plain module-level dicts, not state vars.
Reflex's default var cache only tracks *state var* dependencies
(`self.current_customer_id` here), so once ticket/profile edits below
start mutating those dicts in place, a cached var could keep returning
a stale snapshot from before the edit. `cache=False` forces a fresh
read on every state update instead — the right tradeoff at this data
size. (This mutable-shared-dict behavior is also, not coincidentally,
a fairly honest preview of how a real shared database behaves — every
session sees the same underlying data, unlike per-session state.)
"""

import uuid
from datetime import date

import reflex as rx

from rflx_customer_portal.models import (
    SEEDED_CUSTOMERS,
    SEEDED_ORDERS,
    SEEDED_TICKETS,
    Order,
    Ticket,
)
from rflx_customer_portal.states.auth_state import AuthState



class PortalState(AuthState):
    """Data the logged-in customer is allowed to see, and only that data."""

    @rx.var(cache=False)
    def my_orders(self) -> list[Order]:
        return SEEDED_ORDERS.get(self.current_customer_id, [])

    @rx.var(cache=False)
    def my_tickets(self) -> list[Ticket]:
        return SEEDED_TICKETS.get(self.current_customer_id, [])

    @rx.var(cache=False)
    def open_ticket_count(self) -> int:
        return sum(1 for t in self.my_tickets if t.status in ("open", "pending"))

    # Flat profile fields rather than one nested "customer" object — a
    # computed var typed as Optional[Customer] is harder to render safely
    # in components (every field access needs an rx.cond None-check), so
    # this stays simple and explicit for a portal this size.

    @rx.var(cache=False)
    def customer_full_name(self) -> str:
        customer = SEEDED_CUSTOMERS.get(self.current_customer_id)
        return customer.full_name if customer else ""

    @rx.var(cache=False)
    def customer_email(self) -> str:
        customer = SEEDED_CUSTOMERS.get(self.current_customer_id)
        return customer.email if customer else ""

    @rx.var(cache=False)
    def customer_company(self) -> str:
        customer = SEEDED_CUSTOMERS.get(self.current_customer_id)
        return customer.company if customer else ""

    @rx.var(cache=False)
    def customer_plan(self) -> str:
        customer = SEEDED_CUSTOMERS.get(self.current_customer_id)
        return customer.plan if customer else ""

    # ------------------------------------------------------------------
    # Ticket create / update
    #
    # One dialog, one form, two modes ("create" vs "edit") — rather than
    # duplicating near-identical dialogs. Customers can freely edit
    # subject/priority/status here; a real support system would likely
    # restrict status transitions to agents, but that's a policy choice
    # layered on top of this, not a structural change to it.
    # ------------------------------------------------------------------

    ticket_dialog_open: bool = False
    ticket_dialog_mode: str = "create"  # "create" | "edit"
    ticket_form_ticket_id: str = ""  # empty while creating
    ticket_form_subject: str = ""
    ticket_form_priority: str = "medium"
    ticket_form_status: str = "open"
    ticket_form_error: str = ""

    @rx.event
    def set_ticket_dialog_open(self, value: bool):
        self.ticket_dialog_open = value
        if not value:
            self.ticket_form_error = ""

    @rx.event
    def open_create_ticket(self):
        self.ticket_dialog_mode = "create"
        self.ticket_form_ticket_id = ""
        self.ticket_form_subject = ""
        self.ticket_form_priority = "medium"
        self.ticket_form_status = "open"
        self.ticket_form_error = ""
        self.ticket_dialog_open = True

    @rx.event
    def open_edit_ticket(self, ticket_id: str):
        ticket = next(
            (t for t in SEEDED_TICKETS.get(self.current_customer_id, [])
             if t.ticket_id == ticket_id),
            None,
        )
        if ticket is None:
            return
        self.ticket_dialog_mode = "edit"
        self.ticket_form_ticket_id = ticket.ticket_id
        self.ticket_form_subject = ticket.subject
        self.ticket_form_priority = ticket.priority
        self.ticket_form_status = ticket.status
        self.ticket_form_error = ""
        self.ticket_dialog_open = True

    @rx.event
    def set_ticket_form_subject(self, value: str):
        self.ticket_form_subject = value

    @rx.event
    def set_ticket_form_priority(self, value: str):
        self.ticket_form_priority = value

    @rx.event
    def set_ticket_form_status(self, value: str):
        self.ticket_form_status = value

    @rx.event
    def save_ticket(self):
        subject = self.ticket_form_subject.strip()
        if not subject:
            self.ticket_form_error = "Subject is required."
            return

        customer_tickets = SEEDED_TICKETS.setdefault(self.current_customer_id, [])

        if self.ticket_dialog_mode == "create":
            customer_tickets.append(
                Ticket(
                    ticket_id=f"tkt_{uuid.uuid4().hex[:6]}",
                    customer_id=self.current_customer_id,
                    subject=subject,
                    status="open",
                    priority=self.ticket_form_priority,
                    opened_on=date.today().isoformat(),
                )
            )
        else:
            for ticket in customer_tickets:
                if ticket.ticket_id == self.ticket_form_ticket_id:
                    ticket.subject = subject
                    ticket.priority = self.ticket_form_priority
                    ticket.status = self.ticket_form_status
                    break

        self.ticket_form_error = ""
        self.ticket_dialog_open = False

    # ------------------------------------------------------------------
    # Profile editing
    #
    # Full name / email / company are customer-editable. Username and
    # plan are deliberately left out: username is the login identity
    # (changing it here would be a re-auth concern), and plan changes
    # would realistically go through a billing/upgrade flow rather than
    # a plain profile edit — both stay read-only in the UI.
    # ------------------------------------------------------------------

    edit_full_name: str = ""
    edit_email: str = ""
    edit_company: str = ""
    profile_form_error: str = ""
    profile_save_message: str = ""

    @rx.event
    def on_account_load(self):
        """Combined on_load for /account: auth guard + form hydration.

        Kept as a single handler (rather than a list passed to on_load)
        to sidestep any version uncertainty around multi-handler on_load
        lists — one handler per page is unambiguous either way.
        """
        if not self.is_authenticated:
            return rx.redirect("/login")

        customer = SEEDED_CUSTOMERS.get(self.current_customer_id)
        if customer:
            self.edit_full_name = customer.full_name
            self.edit_email = customer.email
            self.edit_company = customer.company
        self.profile_form_error = ""
        self.profile_save_message = ""
        return None

    @rx.event
    def set_edit_full_name(self, value: str):
        self.edit_full_name = value
        self.profile_save_message = ""

    @rx.event
    def set_edit_email(self, value: str):
        self.edit_email = value
        self.profile_save_message = ""

    @rx.event
    def set_edit_company(self, value: str):
        self.edit_company = value
        self.profile_save_message = ""

    @rx.event
    def save_profile(self):
        customer = SEEDED_CUSTOMERS.get(self.current_customer_id)
        if customer is None:
            return

        full_name = self.edit_full_name.strip()
        email = self.edit_email.strip()
        company = self.edit_company.strip()

        if not full_name or not email:
            self.profile_form_error = "Name and email are required."
            self.profile_save_message = ""
            return

        customer.full_name = full_name
        customer.email = email
        customer.company = company

        self.profile_form_error = ""
        self.profile_save_message = "Saved."
