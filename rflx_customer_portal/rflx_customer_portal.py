"""Customer portal — main app entry point.

Registers pages by importing them (the `@rx.page(...)` decorator on each
page function registers its route at import time), then instantiates the
Reflex App. The root route redirects straight into the app; there's no
separate marketing/landing page for this build.
"""

import reflex as rx

# Importing these triggers their @rx.page(...) route registration.
from rflx_customer_portal.pages import account, dashboard, login  # noqa: F401


def index() -> rx.Component:
    return rx.fragment()


app = rx.App()
app.add_page(index, route="/", on_load=rx.redirect("/dashboard"))
