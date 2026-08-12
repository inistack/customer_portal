# Customer Portal — Setup Log

## Outcome

A working, self-hosted customer portal built in pure Python with Reflex,
featuring authentication, a per-customer data view, and a documented path
to self-hosted deployment.

## Prerequisites

- **Python 3.10 or newer.** This project uses Python 3.14.4, confirmed
  compatible — Reflex 0.9.7+ lists Python 3.14 as a supported version on
  PyPI (`Requires-Python: >=3.10,<4.0`).
- **uv** (recommended package/env manager). A pip + venv fallback is noted
  below for anyone who doesn't want uv.
- **No database required to start.** The app ships with a simulated,
  seeded in-memory customer dataset (orders/tickets) so the portal is
  fully demonstrable without an external backend. Swapping this for a
  real DB/ORM (e.g. SQLModel + SQLite/Postgres) is a documented, later
  step — not part of the initial build.

## Step-by-step log

### 1. Verify environment

Checked for Python and uv on the target machine:

```bash
python3 --version   # -> Python 3.14.4
uv --version         # -> not found
```

Python 3.14.4 exceeds Reflex's minimum requirement and is explicitly
supported per the current PyPI listing (checked live, not from memory,
since Reflex's own docs skill warns training data on it may be stale).

### 2. Install uv

Not present, so installed via the official Astral installer:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

This installs `uv` and `uvx` into `~/.local/bin` and appends that
directory to `PATH` in `.bashrc` / `.profile` automatically. Restart
your terminal (or `source ~/.bashrc`) to pick it up in new sessions.

Verify:

```bash
uv --version   # -> uv 0.12.2
```

**pip/venv alternative** (if you'd rather not use uv):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install reflex
```

### 3. Scaffold the Reflex app

From `/home/inistack/Dev/REFLEX/rflx_customer_portal`:

```bash
uv init --bare       # creates pyproject.toml, no template files
uv add reflex         # creates .venv, installs Reflex 0.9.8 + deps
uv run reflex init    # scaffolds the app; prompts for a template
```

`reflex init` prompts:

```
Get started with a template:
(0) A blank Reflex app.
(1) Try our AI builder.
Which template would you like to use? (0):
```

Selected **(0) A blank Reflex app** — the starting point the rest of the
Reflex docs assume.

Result: `rflx_customer_portal/rflx_customer_portal.py` (main app file),
`rxconfig.py` (config), `.web/` (generated frontend), `assets/`,
`uv.lock`.

Note: `reflex init` also generates its own project-level `AGENTS.md` /
`CLAUDE.md`, mirroring the same "install and use the reflex-docs /
setup-python-env / reflex-process-management skills" instructions from
the parent `agent-skills` repo. No conflict — same guidance, now
embedded in the project itself.

### 4. Fix a deprecation warning in rxconfig.py

`reflex compile --dry` surfaced:

```
DeprecationWarning: Implicit Radix Themes enablement has been
deprecated in version 0.9.0. Configure `rx.plugins.RadixThemesPlugin()`
in `rxconfig.py` to make this explicit...
```

Fixed by explicitly declaring the plugin in `rxconfig.py`:

```python
import reflex as rx

config = rx.Config(
    app_name="rflx_customer_portal",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
        rx.plugins.RadixThemesPlugin(),
    ]
)
```

### 5. Validate the app compiles

```bash
uv run reflex compile --dry
```

Result: `Success: App compiled successfully.` — no errors, no warnings.

### 6. Run the server and confirm it's reachable

Per the `reflex-process-management` skill, production mode is the
default unless dev mode is explicitly requested:

```bash
uv run reflex run --env prod --single-port 2>&1 | tee reflex.log
```

**First run only:** Reflex downloads a local Bun runtime
(`~/.local/share/reflex/bun`) and then uses it to install frontend
build dependencies (Vite, Tailwind, React Router, etc.) into `.web/`.
On a slow connection this can take several minutes — subsequent runs
skip this step entirely. Once it finishes, `reflex.log` will contain:

```
App running at: http://0.0.0.0:<port>
```

Open that in a browser to confirm the blank app loads.

**To reload after code changes** (prod mode has no hot reload):

```bash
lsof -i :<port> -sTCP:LISTEN -t                  # find listening process
kill -INT $(lsof -i :<port> -sTCP:LISTEN -t)     # graceful stop
> reflex.log
uv run reflex run --env prod --single-port 2>&1 | tee reflex.log
```

### 7. Troubleshooting note: first prod-mode run failed

The very first `--env prod --single-port` attempt (run while Bun was
still mid-download) errored on every request:

```
RuntimeError: StaticFiles directory
'.../rflx_customer_portal/.web/build/client' does not exist.
```

Cause: the production build step ran before the frontend dependency
install (`bun add ...`) had actually finished, so `.web/build/client`
was never generated. The process eventually exited on its own rather
than hanging — no manual cleanup was needed once dependencies finished
installing.

### 8. Confirmed working (dev mode)

Once frontend dependencies finished installing, `uv run reflex run`
(default dev mode) was started in its own terminal and confirmed
working in the browser:

- Backend: `python .../reflex run` listening on `:8000`
- Frontend: Bun → `react-router dev --host` listening on `:3000`
- `http://localhost:3000` renders the default "Welcome to Reflex!"
  blank-template page — confirmed via screenshot.

**Decision:** for the remaining build phases (state, auth, UI), we'll
develop against **dev mode** (`uv run reflex run`), since hot reload
matters more than production parity while iterating. A clean
**production-mode** run (`--env prod --single-port`) will be re-verified
as its own step later, once the app has real content and we're closer
to the self-hosting/deployment section — now that Bun's dependency
cache is warm, that re-run should be fast and shouldn't hit the same
race condition.

## Coding phase

### 9. Data models and seeded dataset — `models.py`

Three plain `@dataclass` types: `Customer`, `Order`, `Ticket`. Reflex's
current "Custom Vars" docs recommend dataclasses over pydantic/`rx.Base`
for this purpose (checked live rather than assumed), so that's what's
used here instead of the older `rx.Base` pattern seen in older examples.

Seeded data lives in three module-level dicts, all keyed by
`customer_id`:

```python
SEEDED_CUSTOMERS: dict[str, Customer]
SEEDED_ORDERS: dict[str, list[Order]]
SEEDED_TICKETS: dict[str, list[Ticket]]
```

Two seeded demo customers (`acme` / `brightleaf`), each with their own
orders and tickets, so per-customer scoping is actually visible when you
log in as one vs. the other.

`find_customer_by_username()` does a case-insensitive lookup — this
function's *body* is the only thing that changes when swapping in a
real database (see "Swapping the seeded dataset" below); its signature
and what calls it stay the same.

**Small fix worth noting:** `Order.amount_usd` is a float, but
formatting it with `f"${order.amount_usd:.2f}"` inside a component
doesn't reliably compile — that formatting has to happen at Python
level, not deferred to the browser, and a Reflex Var doesn't support
`:.2f`-style format specs at render time. Fixed by adding a
pre-formatted `amount_display: str` field, computed once in Python via
`__post_init__` at seed time, and rendering that string directly instead.

### 10. The reactive-state model — `states/auth_state.py`, `states/portal_state.py`

Quick primer, for reference:

- **Base vars** — plain fields on a `rx.State` subclass. The only vars
  that event handlers may assign to directly.
- **Computed vars** — `@rx.var`-decorated methods. Recalculated
  automatically whenever a base var they depend on changes; can't be
  set directly.
- **Event handlers** — `@rx.event`-decorated methods. The only way to
  change base vars, triggered by UI props like `on_click` / `on_change`.

**`AuthState(rx.State)`** — the session layer:

- Base vars: `login_username`, `login_password`, `login_error`,
  `is_authenticated`, `current_customer_id`.
- Event handlers: `login` (validates against `find_customer_by_username`,
  sets the session vars, redirects to `/dashboard`), `logout` (clears
  the session, redirects to `/login`), `require_login` (an `on_load`
  guard used by protected pages — redirects to `/login` if there's no
  active session).

**`PortalState(AuthState)`** — the per-customer data layer. It
*inherits* `AuthState` rather than starting fresh from `rx.State`,
because Reflex's state-structure docs specifically recommend inheriting
from a parent state only when the parent holds data the substate
commonly needs — here, `current_customer_id`.

Computed vars: `my_orders`, `my_tickets`, `open_ticket_count`, and flat
profile fields (`customer_full_name`, `customer_email`,
`customer_company`, `customer_plan`). Every one of these is a fresh
dict lookup keyed by `self.current_customer_id` — nothing is
pre-computed or cached at compile time.

**Swapping the seeded dataset for a real database:** because every
lookup already goes through `customer_id`, the swap is contained to two
places — `find_customer_by_username()` in `models.py`, and the bodies
of `my_orders` / `my_tickets` in `portal_state.py`. Replace the dict
lookups with SQLModel queries (e.g.
`select(Order).where(Order.customer_id == customer_id)`), keep the
function/computed-var signatures the same, and nothing upstream (pages,
components, auth flow) needs to change.

### 11. The auth pattern — session state, login form, gating

This is a **local, seeded-credential** auth pattern — session state,
a login form, and gated views — not a production auth system. Two
things worth being explicit about:

1. **`pages/login.py`** — a plain form (username/password inputs bound
   to `AuthState`, submit button calling `AuthState.login`), plus a
   visible "demo login" hint showing the two seeded username/password
   pairs (`acme` / `demo1234`, `brightleaf` / `demo1234`). That hint is
   demo-only scaffolding — it goes away entirely once real auth
   (Clerk) is wired in.
2. **Protected pages** (`/dashboard`, `/account`) use
   `on_load=AuthState.require_login` to redirect unauthenticated
   visitors to `/login`.

**Important nuance, straight from Reflex's own authentication docs:**
that `on_load` redirect is a UX convenience, *not* the actual security
boundary. Anything statically rendered into a page — hardcoded content,
or values computed at compile time — is visible in the page source to
anyone, authenticated or not, even behind a redirect or an `rx.cond`.
The real protection here is that `PortalState`'s computed vars only
return real data when `current_customer_id` is set on the server-side
session — an unauthenticated session has nothing to look up, so there's
nothing to leak, independent of whether the redirect fires.

### 12. Portal UI — dashboard, account, navigation

- **`components/navbar.py`** — shared top nav on every protected page:
  brand, Dashboard/Account links, current customer's name (pulled from
  `PortalState.customer_full_name`), and a logout button.
- **`pages/dashboard.py`** — welcome heading, an open-ticket-count
  summary line, and a tabbed view (`rx.tabs`) switching between an
  Orders table and a Tickets table. Both tables are built with
  `rx.foreach` over the corresponding `PortalState` computed var, with
  a small `_status_badge()` helper using `rx.match` to color-code
  status values (delivered/resolved → green, shipped/pending → blue,
  open → amber, cancelled → red).
- **`pages/account.py`** — a simple read-only profile view (name,
  email, company, plan) built from `PortalState`'s flat profile vars.
- **`rflx_customer_portal.py`** (main entry) — imports the three page
  modules (which self-register their routes via `@rx.page(...)` at
  import time), then registers `/` to redirect straight to
  `/dashboard`. There's no separate marketing/landing page in this
  build.

### 13. Clerk — installed and scaffolded, not active yet

Per the earlier decision: build working local auth now, leave the
portal structured so real Clerk auth is a contained swap once API keys
arrive, rather than fully wiring Clerk with empty keys (which would
just break the demo).

```bash
uv add reflex-clerk-api python-dotenv
```

Installed: `reflex-clerk-api` (wraps Clerk's React SDK + the official
`clerk-backend-api` Python package) and `python-dotenv` (for loading
`.env`).

What's in place:

- **`.env.example`** — placeholders for `CLERK_PUBLISHABLE_KEY` and
  `CLERK_SECRET_KEY`, with a comment pointing at the Clerk dashboard.
- **`.gitignore`** — added `.env` so real keys, once added, are never
  committed.
- **`rflx_customer_portal/clerk_auth.py`** — a real, working module
  (imports cleanly, not commented-out placeholder code) that:
  - loads `.env` via `python-dotenv`
  - exposes `CLERK_ENABLED` (`True` only once both keys are non-empty)
  - `wrap_app_with_clerk(child)` — wraps a component tree in
    `clerk.clerk_provider(...)`
  - `install_auth_pages(app)` — registers Clerk's own `/sign-in` and
    `/sign-up` pages via `clerk.add_sign_in_page` /
    `clerk.add_sign_up_page`

This module is **not yet imported** by `rflx_customer_portal.py` — the
portal currently runs entirely on the local `AuthState` from step 11.

**When real Clerk API keys are available**, the swap-over (documented
in full at the top of `clerk_auth.py`):

1. Get keys from the Clerk dashboard → API Keys page.
2. Copy `.env.example` to `.env`, fill in both keys.
3. In `rflx_customer_portal.py`: wrap `app` with
   `clerk_auth.wrap_app_with_clerk(...)` and call
   `clerk_auth.install_auth_pages(app)`.
4. In `auth_state.py` / `portal_state.py`: replace
   `AuthState.is_authenticated` / `current_customer_id` checks with
   `reflex_clerk_api.ClerkState.is_logged_in` and a lookup keyed by the
   Clerk user's email (or `user_id`) instead of the seeded
   username/password pair.
5. Delete `pages/login.py` and the login-form vars in `AuthState`.
6. If a real DB is in place by then, match Clerk users to customer
   records by email, or store the Clerk `user_id` directly on the
   `customers` row.

### 14. Troubleshooting notes from this phase

- **Auto-generated setters were off.** Reflex normally auto-generates a
  `set_<varname>` event handler for every base var. In this version
  that's gated by a `state_auto_setters` config flag which defaults to
  disabled, so `on_change=AuthState.set_login_username` failed at
  compile time with `AttributeError`. Fixed by writing explicit
  `set_login_username` / `set_login_password` event handlers by hand —
  more explicit anyway, and doesn't depend on that config default.
- **Removed an invalid inline event-trigger pattern.** An earlier draft
  of the login page tried
  `on_key_down=lambda key: rx.cond(key == "Enter", AuthState.login, rx.noop())`
  to submit on Enter. `rx.cond` inside a lambda isn't valid event-trigger
  syntax in Reflex. Removed in favor of plain button-click submission —
  correct over clever, especially before this has been run once.

### 15. Validation performed

```bash
uv run reflex compile --dry
```
→ `Success: App compiled successfully.` (this executes every page
function's component tree in real Python, which is what caught both
issues above).

With the dev server already running (hot-reloaded automatically),
checked each route was actually reachable and free of server errors:

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000/login      # 200
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000/dashboard  # 200
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000/account    # 200
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000/           # 200
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/ping       # 200
```

No genuine error strings in the rendered HTML (the one "error" match
found was React Router's own SSR context payload key name, not an
actual error).

## Feature addition: ticket create/update, profile editing

Requested after the first end-to-end login/logout test passed. Two new
capabilities layered onto the existing state/UI from steps 9–13, plus
one important correctness fix that came with them.

### 16. `cache=False` on the data-reading computed vars

Once tickets and profile fields can be *mutated* (not just read),
`portal_state.py`'s computed vars needed a second look. Reflex's
default var cache (`cache=True`) only recomputes when a *state var* the
var depends on changes — but `my_orders`, `my_tickets`,
`open_ticket_count`, and the `customer_*` profile vars all read from
plain module-level dicts (`SEEDED_TICKETS`, `SEEDED_CUSTOMERS`), not
state vars. Mutating a `Ticket`/`Customer` object in place wouldn't
have reliably invalidated a cached result. Switched all of them to
`@rx.var(cache=False)` so every state update re-reads the underlying
dict fresh. At this data size the recompute cost is irrelevant; the
correctness guarantee matters more.

Worth noting as a design point, not just a workaround: mutating a
shared module-level dict from an event handler affects *all* sessions
using the running server process, not just the current user's — which
is actually a fair preview of how a real shared database behaves
(one source of truth, not a per-session copy). Per-session `rx.State`
alone wouldn't have modeled that correctly.

### 17. Ticket create/update — `PortalState`, `pages/dashboard.py`

One dialog, one `save_ticket` handler, two modes (`"create"` /
`"edit"`) — rather than a separate create form and edit form. New state:
`ticket_dialog_open`, `ticket_dialog_mode`, `ticket_form_ticket_id`,
`ticket_form_subject`, `ticket_form_priority`, `ticket_form_status`,
`ticket_form_error`.

- `open_create_ticket()` resets the form to blank defaults and opens
  the dialog in `"create"` mode.
- `open_edit_ticket(ticket_id)` looks up that ticket in
  `SEEDED_TICKETS[current_customer_id]`, pre-fills the form from it,
  opens the dialog in `"edit"` mode.
- `save_ticket()` validates the subject is non-empty, then either
  appends a new `Ticket` (id via `uuid4().hex[:6]`, status forced to
  `"open"`, `opened_on` set to today) or mutates the matching ticket's
  `subject` / `priority` / `status` in place.

UI: "New ticket" button above the Tickets table opens the create
dialog; each row gets an "Edit" button
(`on_click=lambda: PortalState.open_edit_ticket(ticket.ticket_id)`)
that opens the same dialog pre-filled. The Status field only appears in
edit mode — a ticket doesn't have a status to set before it exists.

**Scope decision:** customers can freely edit priority/status on their
own tickets in this build. A real support system would likely restrict
status transitions to agents (e.g. a customer probably shouldn't be
able to mark their own ticket "resolved" if an agent is still working
it) — that's a policy layer to add later, not a structural limitation
of what's built here.

### 18. Profile editing — `PortalState`, `pages/account.py`

New state: `edit_full_name`, `edit_email`, `edit_company`,
`profile_form_error`, `profile_save_message`.

`/account`'s `on_load` now points at a single new combined handler,
**`PortalState.on_account_load`**, instead of `AuthState.require_login`
directly — it does the same auth-guard redirect *and* hydrates the
edit fields from the current customer record in one handler. (Chose one
combined handler per page over passing a list of handlers to `on_load`,
since I hadn't independently confirmed multi-handler `on_load` lists
behave as expected on this exact Reflex version — a single handler
sidesteps that question entirely rather than assuming.)

`save_profile()` validates name/email are non-empty, then mutates the
`Customer` object's `full_name` / `email` / `company` in place and sets
a "Saved." confirmation message.

**Deliberately left out of the editable fields:** `username` (it's the
login identity — changing it here would be a re-auth/identity concern
beyond this form's scope) and `plan` (shown as a read-only badge; plan
changes would realistically go through a billing/upgrade flow, not a
plain profile edit).

### 19. Re-validated

```bash
uv run reflex compile --dry
```
→ clean compile, no errors.

With the dev server hot-reloading automatically, re-confirmed all
routes still serve (`/`, `/login`, `/dashboard`, `/account` → 200,
backend `/ping` → 200).

## Up next (not yet started)

- **Manual browser verification of the new features** — login/logout
  was confirmed working end-to-end before this feature addition; the
  new ticket create/edit dialog and profile-editing form on `/account`
  haven't been clicked through in the browser yet.
- **Production-mode re-verification** (deferred from step 8) —
  `--env prod --single-port`, now that Bun's cache is warm.
- **Self-hosting guide** — Docker + reverse proxy config, plus notes on
  Reflex Cloud deploy as the alternative (not deployed live — config
  and guide only, per earlier agreement).
- **Real Clerk activation** — once API keys are provided, following the
  swap-over steps in step 13 / `clerk_auth.py`.
- **Real database swap** — documented pattern only (step 10); not
  implemented in this build, per earlier agreement.
