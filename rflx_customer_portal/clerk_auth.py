"""Clerk auth scaffold — not active yet, ready to wire in once real API
keys are provided.

This file is intentionally NOT imported by rflx_customer_portal.py yet.
The portal currently runs on the local seeded-credential AuthState
(see states/auth_state.py). This module exists so the swap-over to real
Clerk auth is a contained, well-marked change rather than a rewrite.

------------------------------------------------------------------------
Swapping in real Clerk auth — steps
------------------------------------------------------------------------
1. Get your keys from https://dashboard.clerk.com (API Keys page).
2. Copy `.env.example` to `.env` and fill in CLERK_PUBLISHABLE_KEY /
   CLERK_SECRET_KEY. `.env` is already gitignored.
3. In rflx_customer_portal.py:
     - import this module: `from rflx_customer_portal import clerk_auth`
     - wrap `app` with `clerk_auth.wrap_app_with_clerk(app)` (below)
     - call `clerk_auth.install_auth_pages(app)` instead of relying on
       the local /login page
4. In states/auth_state.py and states/portal_state.py:
     - replace `AuthState.is_authenticated` checks with
       `reflex_clerk_api.ClerkState.is_logged_in`
     - replace `AuthState.current_customer_id` with a lookup keyed by
       `reflex_clerk_api.ClerkState.user.email` (or `.user_id`) instead
       of the seeded username/password pair
5. Delete pages/login.py and the login-form-specific vars in
   AuthState once ClerkState fully replaces it.
6. If a real DB is also in place by then, match Clerk users to customer
   records by email (or store the Clerk user_id directly on the
   `customers` row going forward, instead of matching on email).
------------------------------------------------------------------------
"""

import os

import reflex as rx
import reflex_clerk_api as clerk
from dotenv import load_dotenv

load_dotenv()

CLERK_PUBLISHABLE_KEY = os.environ.get("CLERK_PUBLISHABLE_KEY", "")
CLERK_SECRET_KEY = os.environ.get("CLERK_SECRET_KEY", "")

# True only once both keys are actually present — lets callers guard
# on this instead of trying to parse empty-string key errors from Clerk.
CLERK_ENABLED = bool(CLERK_PUBLISHABLE_KEY) and bool(CLERK_SECRET_KEY)


def wrap_app_with_clerk(child: rx.Component) -> rx.Component:
    """Wrap a page/component tree in Clerk's provider.

    Only call this once real keys are set — see CLERK_ENABLED above.
    """
    return clerk.clerk_provider(
        child,
        publishable_key=CLERK_PUBLISHABLE_KEY,
        secret_key=CLERK_SECRET_KEY,
        register_user_state=True,
    )


def install_auth_pages(app: rx.App) -> None:
    """Register Clerk's own /sign-in and /sign-up pages on the app."""
    clerk.add_sign_in_page(app)
    clerk.add_sign_up_page(app)
