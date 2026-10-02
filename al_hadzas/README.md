# AL-HADZAS COLLECTIONS — Flet MVP

A runnable Python/Flet implementation of the AL-HADZAS COLLECTIONS coursework
e-commerce platform (see the accompanying Idea & Validation, Feasibility
Study, and Requirements Specification reports). This is a **single-process,
in-memory demo** meant to prove the product concept and the required
technical components — it is not wired to a real database, real payment
gateway, or real antivirus engine (see "What's simulated vs real" below).

## Quick start

```bash
pip install -r requirements.txt
flet run --web main.py
```

Flet will print a local URL (typically `http://localhost:8550`) — open it in
a browser. The console also prints demo login credentials on startup:

| Role   | Email                  | Password     |
|--------|------------------------|--------------|
| Admin  | admin@alhadzas.com     | Admin#1234   |
| Vendor | amina@alhadzas.com     | Vendor#1234  |
| Vendor | kwame@alhadzas.com     | Vendor#1234  |
| Buyer  | buyer@alhadzas.com     | Buyer#1234   |

The app was built and verified against **Flet 0.28.3** specifically (pinned
in `requirements.txt`) — Flet 1.x changed its widget API significantly
(no more `ElevatedButton`/`BarChart`/etc.), so installing a different major
version will break this code.

## Project structure

```
al_hadzas/
  main.py                    # entry point + route table
  requirements.txt
  core/
    data_store.py             # domain models + in-memory store (see complexity notes below)
    security.py                # OWASP-aligned auth/validation/antivirus helpers
    search.py                   # offline TF-IDF semantic search (RAG "retrieval" half)
    chatbot.py                   # CRM chatbot (RAG "generation" half, templated + grounded)
    payment.py                    # simulated payment + cost/"micro component" breakdown
    legal_content.py               # Terms, Privacy, Returns policy text
    seed_data.py                    # demo accounts + starter catalogue
  ui/
    theme.py, state.py               # shared styling + session/cart helpers
    walkthrough.py                    # onboarding (Jakob's Law, see below)
    auth_view.py                       # login / register
    home_view.py                        # catalogue + semantic search + filters
    product_view.py                      # product detail, Culture Notes, sizing, reviews
    cart_view.py, checkout_view.py        # cart + checkout + simulated payment
    orders_view.py                         # buyer order tracking + reviews
    vendor_dashboard.py                     # product CRUD + upload AV scan + order queue
    admin_dashboard.py                       # analytics dashboard + vendor approval + audit log
    chatbot_view.py, legal_view.py            # chat UI, legal document pages
```

## Feature coverage checklist (maps to the Requirements Specification)

- [x] Terms & Conditions, Privacy Policy, Return/Refund Policy pages (`/legal/...`)
- [x] RAG-style semantic search: TF-IDF retrieval (`core/search.py`) feeding both the
      catalogue search bar and the CRM chatbot's product lookups
- [x] OWASP Top-10-aligned controls (`core/security.py` — see annotated categories)
- [x] One HCI law selected and deliberately applied: **Jakob's Law** (see below)
- [x] Onboarding walkthrough (`ui/walkthrough.py`)
- [x] Dashboard & analytics (`ui/admin_dashboard.py` — bar + pie charts, KPIs, audit log)
- [x] Payment + cost/"micro components" breakdown (`core/payment.py`, shown on cart & checkout)
- [x] CRM chatbot (`core/chatbot.py`, `ui/chatbot_view.py`)
- [x] "Antivirus" upload security control (`core/security.py::AntivirusScanner`)
- [x] All custom algorithms/data structures are O(n) or O(n log n) (see below)

## HCI law applied: Jakob's Law

> "Users spend most of their time on sites other than yours, so they prefer
> your site to work the same way as the sites they already know."

**Why this law, specifically, for this product:** the Idea & Validation
research identified *buyer trust in an unfamiliar niche storefront* as the
single biggest adoption risk — people are being asked to prepay for
custom-fitted clothing from a small vendor they've never heard of. The
fastest lever to earn that trust is to make every *mechanical* part of the
experience (nav bar, cart icon placement, search bar, filter layout, product
grid, checkout steps, order-status stepper) feel exactly like a mainstream
store they already trust — and spend the platform's "novelty budget" only on
the one place it should go: the cultural storytelling ("Culture Notes"), not
on reinventing how a cart or checkout works. The onboarding walkthrough
(`ui/walkthrough.py`) explicitly tells the first-time user this, operationalising
Jakob's Law as a stated onboarding strategy rather than an implicit design choice.

## OWASP Top 10 (2021) coverage

See the module docstring in `core/security.py` for the full mapping; in short:

| Category | Control |
|---|---|
| A01 Broken Access Control | `require_role()` gates vendor/admin routes; new vendors start unverified |
| A02 Cryptographic Failures | Passwords hashed with per-user salt, PBKDF2-HMAC-SHA256, 260k iterations |
| A03 Injection | `sanitize_text()` / `validate_email()` / `validate_price()` on all user input |
| A04 Insecure Design | `LoginRateLimiter` locks an account after 5 failed logins |
| A05 Security Misconfiguration | Explicit `SecurityConfig` (no silently-trusted defaults) |
| A07 Auth Failures | Opaque, unguessable session tokens (`secrets.token_urlsafe`) with 1hr expiry |
| A08 Software/Data Integrity | `AntivirusScanner` gates every vendor file upload before acceptance |
| A09 Logging & Monitoring | `STORE.audit_log`, surfaced in the admin dashboard |
| A10 SSRF | Not directly applicable (no server-side fetch of user-supplied URLs) — noted for future work |

## Algorithm / data-structure complexity (O(n) / O(n log n) requirement)

All custom logic in this codebase stays within the required bound. The full
reasoning lives as inline comments next to each structure, summarised here:

| Operation | Structure | Complexity |
|---|---|---|
| Get/insert/update a user, product, vendor, or order by id | `dict` (hash table) | **O(1)** |
| Price-range product queries | sorted list + `bisect` | **O(log n)** to locate bounds, O(k) to collect matches |
| "Oldest unfulfilled order" per vendor | `heapq` min-heap | **O(log n)** push/pop |
| Semantic search over the catalogue | TF-IDF vector compare per product | **O(n)** per query |
| Top-k analytics (best sellers, top-k search results) | `heapq.nlargest` | **O(n log k)**, better than a full O(n log n) sort when k ≪ n |
| Catalogue/analytics aggregation (revenue, order-status counts) | single pass | **O(n)** |
| Checkout cost breakdown | single pass over cart items (m ≪ n) | **O(m)**, effectively O(1) relative to catalogue size |

No structure or algorithm in the codebase exceeds O(n log n).

## What's simulated vs. real (by design, per project scope)

| Component | This build | Why |
|---|---|---|
| Semantic search / RAG | Real TF-IDF + cosine similarity, fully offline | No API key required for the coursework demo |
| Payment | Fully simulated (`core/payment.py`), no network call | Avoids requiring real Stripe/Paystack keys |
| Antivirus | Simulated: extension allow-list, size limit, signature/hash check (EICAR test string) | No ClamAV binary required in the grading environment |
| Database | In-memory (`core/data_store.py`), resets on restart | Keeps the coursework demo self-contained; swappable later behind the same `DataStore` interface |
| Legal pages | Sample coursework copy, not lawyer-reviewed | Flagged as a caveat in the Feasibility Study |

## Testing performed before delivery

- `python -m py_compile` on every file (syntax-level check).
- A headless "smoke test" (not included in the delivered zip, but the
  technique is documented here) instantiated every view-construction
  function with a fake Page object and confirmed each returns a valid
  `ft.View` with no exceptions, across buyer/vendor/admin roles and
  empty/non-empty cart states.
- The real Flet web server was started via `flet run`-equivalent code and
  confirmed to serve HTTP 200 with no server-side exceptions.
- End-to-end logic (search, chatbot, payment breakdown, password hashing,
  antivirus scanning) was exercised directly and produced correct results.

A full browser-driven UI test (e.g. Playwright clicking through the actual
flow) was not possible in the sandbox this was built in (no network access
to download a browser binary) — running `flet run --web main.py` yourself
and clicking through the flow is the recommended final check before you
submit or demo this.
