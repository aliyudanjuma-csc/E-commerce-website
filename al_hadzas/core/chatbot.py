"""
core/chatbot.py
-----------------
A small CRM/support chatbot built on top of the semantic search index
(core/search.py). This is the "generation" half of the mini RAG
pipeline: it retrieves the most relevant context (an FAQ answer, a
product, an order, or a legal-policy excerpt) and composes a plain
templated reply from it, rather than free-generating text -- which
keeps answers grounded/traceable, appropriate for a customer-support
bot that must not hallucinate policy details.

Retrieval sources (in priority order):
1. Order-status intent (regex match on an order id) -> O(1) dict lookup.
2. FAQ knowledge base -> TF-IDF semantic search over a small fixed set
   of Q&A pairs, O(n) where n = number of FAQ entries (small, constant).
3. Product catalogue -> TF-IDF semantic search, O(n) over products.
4. Legal documents (terms/privacy/returns) -> keyword-triggered lookup, O(1).

Overall a single chatbot turn is O(n) in the size of the catalogue,
matching the O(n) / O(n log n) constraint for the whole system.
"""

from __future__ import annotations

import re

from core.data_store import STORE
from core.search import SemanticSearchIndex, SearchHit
from core.legal_content import TERMS_AND_CONDITIONS, PRIVACY_POLICY, RETURNS_POLICY

FAQ = [
    {
        "q": "How do I know my size will fit for a made-to-measure order?",
        "a": "Each product page has a standardized sizing guide with step-by-step "
             "measurement instructions. For Made-to-Measure items, enter your own "
             "measurements at checkout and the vendor tailors to those numbers.",
    },
    {
        "q": "Is it safe to pay before my order ships?",
        "a": "Yes. Payments are held by AL-HADZAS COLLECTIONS and only released to the "
             "vendor once your order is marked shipped, and every vendor is verified "
             "by our admin team before they can list products.",
    },
    {
        "q": "How long does international shipping take?",
        "a": "Standard international shipping typically takes 7-14 business days after "
             "the vendor marks your order as shipped. You can track status any time from "
             "'My Orders'.",
    },
    {
        "q": "Can I return a custom made-to-measure garment?",
        "a": "Made-to-measure items are custom-cut and are generally final sale except "
             "for defects; ready-to-wear items can be returned within 14 days. See the "
             "full Return & Refund Policy for details.",
    },
    {
        "q": "How do vendors get verified?",
        "a": "Every tailor/designer submits an application reviewed by an AL-HADZAS admin, "
             "who checks sample work and business details before approving them to sell.",
    },
    {
        "q": "What payment methods are supported?",
        "a": "This coursework build uses a simulated checkout so no real card or bank "
             "details are collected; a production version would add card and mobile-money "
             "gateways.",
    },
]

_ORDER_ID_RE = re.compile(r"\b([A-Z]{2,4}-\d{4,8})\b", re.IGNORECASE)

_faq_index = SemanticSearchIndex()


def _build_faq_index() -> None:
    class _FauxProduct:
        """Wraps an FAQ entry so it can be reused by SemanticSearchIndex,
        which expects objects exposing .searchable_text()."""
        def __init__(self, entry):
            self.entry = entry

        def searchable_text(self):
            return self.entry["q"] + " " + self.entry["a"]

    _faq_index.build([_FauxProduct(e) for e in FAQ])  # O(n), n = len(FAQ)


_build_faq_index()


def _legal_lookup(message: str) -> str | None:
    m = message.lower()
    if "privacy" in m:
        return "Here's a summary of our Privacy Policy:\n\n" + PRIVACY_POLICY[:600] + "\n\n(See the full Privacy Policy page for details.)"
    if "return" in m or "refund" in m:
        return "Here's a summary of our Return & Refund Policy:\n\n" + RETURNS_POLICY[:600] + "\n\n(See the full Returns policy page for details.)"
    if "terms" in m or "condition" in m:
        return "Here's a summary of our Terms & Conditions:\n\n" + TERMS_AND_CONDITIONS[:600] + "\n\n(See the full Terms & Conditions page for details.)"
    return None


def answer(message: str, product_index: SemanticSearchIndex, buyer_id: str | None = None) -> str:
    """Compose a grounded reply for a single chatbot turn. O(n) overall."""
    message = (message or "").strip()
    if not message:
        return "Hi! Ask me about sizing, orders, returns, or say e.g. 'show me Kente styles'."

    # 1) Order status intent -> O(1) dict lookup
    order_match = _ORDER_ID_RE.search(message)
    if order_match:
        order_id = order_match.group(1).upper()
        order = STORE.orders.get(order_id)
        if order:
            return (f"Order {order_id} is currently **{order.status}**. "
                    f"Total paid: ${order.total:.2f}. "
                    f"({len(order.items)} item(s).)")
        return f"I couldn't find an order with id {order_id}. Double-check the id in 'My Orders'."

    # 2) Legal/policy intent -> O(1)
    legal_reply = _legal_lookup(message)
    if legal_reply:
        return legal_reply

    # 3) FAQ retrieval -> O(n_faq), n_faq is small/constant
    faq_hits: list[SearchHit] = _faq_index.search(message, top_k=1, min_score=0.12)
    if faq_hits:
        idx = FAQ.index(faq_hits[0].product.entry) if hasattr(faq_hits[0].product, "entry") else None
        entry = faq_hits[0].product.entry
        return entry["a"]

    # 4) Product retrieval -> O(n_products)
    if product_index.is_ready():
        hits = product_index.search(message, top_k=3, min_score=0.05)
        if hits:
            lines = [f"I found {len(hits)} item(s) that match \"{message}\":"]
            for h in hits:
                lines.append(f"- {h.product.name} ({h.product.country_of_origin}) - ${h.product.price:.2f}")
            return "\n".join(lines)

    return ("I'm not sure about that yet. Try asking about sizing, an order id (e.g. ORD-000123), "
            "shipping, returns, or search for a style like 'wedding Agbada'.")
