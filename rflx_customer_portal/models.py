"""Data models and seeded demo dataset for the customer portal.

This module stands in for a real database. Every customer-facing piece of
data (orders, tickets, profile info) is looked up from the in-memory dicts
below, keyed by `customer_id` — the same shape a real query would need:

    # Today (seeded):
    SEEDED_ORDERS.get(customer_id, [])

    # Later (real DB via SQLModel, for example):
    with rx.session() as session:
        session.exec(
            select(Order).where(Order.customer_id == customer_id)
        ).all()

See setup.md, "Swapping the seeded dataset for a real database", for the
full migration notes.
"""

# from __future__ import annotations

from dataclasses import dataclass

# Reflex's current guidance is to model custom var types as plain
# dataclasses rather than pydantic/rx.Base models (dataclasses are the
# recommended approach per the Reflex "Custom Vars" docs, checked live
# against the current version rather than assumed from memory).


@dataclass
class Customer:
    """A customer account.

    In production this would be a row in a `customers` table — or, once
    real Clerk auth is wired in, synced from Clerk's `User` object instead
    of holding its own password field at all.
    """

    customer_id: str
    username: str
    password: str
    full_name: str
    email: str
    company: str
    plan: str


@dataclass
class Order:
    """A single order belonging to a customer."""

    order_id: str
    customer_id: str
    item: str
    status: str  # "processing" | "shipped" | "delivered" | "cancelled"
    amount_usd: float
    # Pre-formatted for display. Formatting a float Var with a spec like
    # `:.2f` inside an f-string doesn't reliably compile in components
    # (that formatting happens at render time in the browser, not in
    # plain Python), so it's simplest and safest to format once here in
    # real Python at seed time and just render the string in the UI.
    amount_display: str = ""
    placed_on: str = ""  # ISO date string — kept as str to keep the seeded data simple

    def __post_init__(self) -> None:
        if not self.amount_display:
            self.amount_display = f"${self.amount_usd:,.2f}"


@dataclass
class Ticket:
    """A single support ticket belonging to a customer."""

    ticket_id: str
    customer_id: str
    subject: str
    status: str  # "open" | "pending" | "resolved" | "closed"
    priority: str  # "low" | "medium" | "high"
    opened_on: str
    


# ---------------------------------------------------------------------------
# Seeded demo data
#
# NOTE: passwords are plaintext here purely because this is a local,
# throwaway demo dataset with no real customers behind it. Do not carry
# this pattern into a real login system — even a "temporary" real auth
# path should hash passwords (e.g. with passlib) rather than store them
# as-is. This is exactly the kind of thing the Clerk swap-over removes
# entirely, since Clerk owns credential storage.
# ---------------------------------------------------------------------------

SEEDED_CUSTOMERS: dict[str, Customer] = {
    "cust_001": Customer(
        customer_id="cust_001",
        username="user001",
        password="demo1234",
        full_name="Dana Whitfield",
        email="dana@dw.example.com",
        company="Prime Logistics",
        plan="Growth",
    ),
    "cust_002": Customer(
        customer_id="cust_002",
        username="user002",
        password="demo1234",
        full_name="Malik Osei",
        email="malik@mo.example.com",
        company="Sankofa Studio",
        plan="Starter",
    ),
}

SEEDED_ORDERS: dict[str, list[Order]] = {
    "cust_001": [
        Order(
            order_id="ord_1001",
            customer_id="cust_001",
            item="Pallet racking — Bay A",
            status="shipped",
            amount_usd=2450.00,
            placed_on="2026-07-02",
        ),
        Order(
            order_id="ord_1002",
            customer_id="cust_001",
            item="Forklift service contract",
            status="processing",
            amount_usd=890.00,
            placed_on="2026-07-28",
        ),
        Order(
            order_id="ord_1003",
            customer_id="cust_001",
            item="Warehouse signage kit",
            status="delivered",
            amount_usd=310.50,
            placed_on="2026-06-14",
        ),
    ],
    "cust_002": [
        Order(
            order_id="ord_2001",
            customer_id="cust_002",
            item="Studio lighting rig",
            status="delivered",
            amount_usd=1250.00,
            placed_on="2026-05-30",
        ),
        Order(
            order_id="ord_2002",
            customer_id="cust_002",
            item="Editing workstation upgrade",
            status="cancelled",
            amount_usd=3199.00,
            placed_on="2026-06-20",
        ),
    ],
}

SEEDED_TICKETS: dict[str, list[Ticket]] = {
    "cust_001": [
        Ticket(
            ticket_id="tkt_5001",
            customer_id="cust_001",
            subject="Delayed delivery on ord_1002",
            status="open",
            priority="high",
            opened_on="2026-08-01",
        ),
        Ticket(
            ticket_id="tkt_5002",
            customer_id="cust_001",
            subject="Invoice copy request",
            status="resolved",
            priority="low",
            opened_on="2026-07-10",
        ),
    ],
    "cust_002": [
        Ticket(
            ticket_id="tkt_6001",
            customer_id="cust_002",
            subject="Refund status for ord_2002",
            status="pending",
            priority="medium",
            opened_on="2026-06-22",
        ),
    ],
}


def find_customer_by_username(username: str) -> Customer | None:
    """Look up a seeded customer by username (case-insensitive).

    Mirrors the shape of a future
    `SELECT * FROM customers WHERE username = :username` query — swapping
    this function's body is the only change needed upstream in AuthState.
    """
    normalized = username.strip().lower()
    for customer in SEEDED_CUSTOMERS.values():
        if customer.username.lower() == normalized:
            return customer
    return None
