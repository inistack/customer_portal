"""Session / auth state for the customer portal.

This is the "demonstrates the auth pattern" layer: session state, a login
event handler, and a logout event handler. It runs entirely on seeded
local credentials — no external service required to try the app.

Real protection note (from Reflex's own auth docs, checked live): any
content baked statically into a page — hardcoded text, or data computed
at compile time — is visible in the page source to anyone, authenticated
or not, even if the page *looks* gated behind a redirect. The actual
security boundary here is that customer data (see PortalState) only ever
comes from *state*, and state vars are computed fresh per user session on
the server. An unauthenticated session simply has no `current_customer_id`
to look anything up with, so there's nothing to leak — the redirect below
is a UX convenience on top of that, not the protection mechanism itself.

Swapping in real Clerk auth later replaces this whole file with
`reflex_clerk_api.ClerkState` — see the "Swapping in real Clerk auth"
section of setup.md and `clerk_auth.py` for the scaffolded provider.
"""

import reflex as rx

from rflx_customer_portal.models import find_customer_by_username


class AuthState(rx.State):
    """Holds the logged-in session for the current browser tab."""

    # Login form fields (base vars — only these may be set directly).
    login_username: str = ""
    login_password: str = ""
    login_error: str = ""

    # Session vars.
    is_authenticated: bool = False
    current_customer_id: str = ""

    @rx.event
    def set_login_username(self, value: str):
        self.login_username = value

    @rx.event
    def set_login_password(self, value: str):
        self.login_password = value

    @rx.event
    def login(self):
        """Validate the seeded credentials and start a session."""
        customer = find_customer_by_username(self.login_username)
        if customer is None or customer.password != self.login_password:
            self.login_error = "Invalid username or password."
            return None

        self.is_authenticated = True
        self.current_customer_id = customer.customer_id
        self.login_error = ""
        # Don't keep the submitted password sitting in state any longer
        # than it takes to check it.
        self.login_password = ""
        return rx.redirect("/dashboard")

    @rx.event
    def logout(self):
        """End the session and send the customer back to login."""
        self.is_authenticated = False
        self.current_customer_id = ""
        self.login_username = ""
        self.login_password = ""
        return rx.redirect("/login")

    @rx.event
    def require_login(self):
        """`on_load` guard for protected pages.

        Redirects to /login if there's no active session. This is the UX
        guard, not the security boundary — see module docstring.
        """
        if not self.is_authenticated:
            return rx.redirect("/login")
        return None
