"""
core/data_store.py
-------------------
Domain models (Product, Vendor, User, Order, Review) and an in-memory
DataStore that backs the whole coursework MVP.

ALGORITHM / DATA STRUCTURE NOTES (see README for full write-up)
-----------------------------------------------------------------
- Products, Users, Vendors, Orders are all kept in `dict`s keyed by id.
  -> get/insert/delete/update on any single record is O(1) average case
     (Python dict = hash table).
- `products_by_price` is a list kept sorted by price using `bisect.insort`.
  -> Range/price queries use `bisect_left`/`bisect_right` = O(log n) to
     find the boundary, then a linear O(k) scan over the k matching
     items (k <= n). Insertion is O(log n) to find the slot + O(n) worst
     case to shift the underlying array (documented, still within the
     "O(n)" bound required by the brief).
- `_vendor_order_queue` is a `heapq` (binary min-heap) keyed by order
  timestamp, used by the vendor dashboard to always show the oldest
  unfulfilled order first without re-sorting the whole list each time.
  -> push/pop = O(log n), peek = O(1).
- Full-catalogue scans (search, analytics aggregation) are a single
  pass over all n products/orders = O(n).
- "Top-k" analytics (best sellers, top vendors) use `heapq.nlargest`,
  which is O(n log k) rather than sorting the whole collection
  (O(n log n)) -> strictly better when k << n, and still within the
  O(n log n) bound when k ~ n.
"""

from __future__ import annotations

import itertools
import time
import bisect
import heapq
from dataclasses import dataclass, field
from typing import Optional


_id_counter = itertools.count(1)


def next_id(prefix: str) -> str:
    """O(1) id generator."""
    return f"{prefix}-{next(_id_counter):06d}"


# ---------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------

@dataclass
class User:
    id: str
    name: str
    email: str
    password_hash: str
    salt: str
    role: str  # "buyer" | "vendor" | "admin"
    created_at: float = field(default_factory=time.time)
    failed_login_attempts: int = 0
    locked_until: float = 0.0


@dataclass
class Vendor:
    id: str
    user_id: str
    business_name: str
    country: str
    verified: bool = False
    rating_total: float = 0.0
    rating_count: int = 0

    @property
    def rating(self) -> float:
        return round(self.rating_total / self.rating_count, 2) if self.rating_count else 0.0


@dataclass
class Product:
    id: str
    vendor_id: str
    name: str
    description: str          # used as the "Culture Notes" text
    fabric: str
    country_of_origin: str
    occasion: str
    price: float
    sizes: list[str]
    stock: int
    image_note: str = "placeholder-image"
    created_at: float = field(default_factory=time.time)

    def searchable_text(self) -> str:
        return " ".join([
            self.name, self.description, self.fabric,
            self.country_of_origin, self.occasion,
        ])


@dataclass
class OrderItem:
    product_id: str
    name: str
    unit_price: float
    quantity: int
    size: str


@dataclass
class Order:
    id: str
    buyer_id: str
    vendor_id: str
    items: list[OrderItem]
    subtotal: float
    commission_fee: float
    payment_processing_fee: float
    shipping_fee: float
    total: float
    status: str = "placed"  # placed -> processing -> shipped -> delivered
    created_at: float = field(default_factory=time.time)
    history: list[tuple[str, float]] = field(default_factory=list)


@dataclass
class Review:
    id: str
    product_id: str
    buyer_id: str
    rating: int  # 1-5
    comment: str
    created_at: float = field(default_factory=time.time)


# ---------------------------------------------------------------------
# In-memory data store
# ---------------------------------------------------------------------

class DataStore:
    """Single in-process store. Swappable for a real DB layer later
    without changing the UI code, since every access goes through the
    methods below.
    """

    def __init__(self):
        self.users: dict[str, User] = {}
        self.users_by_email: dict[str, str] = {}   # email -> user_id, O(1)
        self.vendors: dict[str, Vendor] = {}
        self.products: dict[str, Product] = {}
        self.orders: dict[str, Order] = {}
        self.reviews: dict[str, list[Review]] = {}  # product_id -> [Review]

        # sorted-by-price index: list of (price, product_id) kept sorted
        self._products_by_price: list[tuple[float, str]] = []

        # min-heap of (created_at, order_id) per vendor for O(log n)
        # "oldest unfulfilled order" retrieval
        self._vendor_queues: dict[str, list[tuple[float, str]]] = {}

        self.audit_log: list[dict] = []  # NFR-12 auditability

    # ---------------- Users ----------------
    def add_user(self, user: User) -> None:
        self.users[user.id] = user               # O(1)
        self.users_by_email[user.email.lower()] = user.id  # O(1)

    def get_user_by_email(self, email: str) -> Optional[User]:
        uid = self.users_by_email.get(email.lower())  # O(1)
        return self.users.get(uid) if uid else None

    # ---------------- Vendors ----------------
    def add_vendor(self, vendor: Vendor) -> None:
        self.vendors[vendor.id] = vendor          # O(1)
        self._vendor_queues[vendor.id] = []

    # ---------------- Products ----------------
    def add_product(self, product: Product) -> None:
        self.products[product.id] = product       # O(1)
        bisect.insort(self._products_by_price, (product.price, product.id))  # O(log n) find + O(n) shift

    def remove_product(self, product_id: str) -> None:
        p = self.products.pop(product_id, None)   # O(1)
        if p:
            idx = bisect.bisect_left(self._products_by_price, (p.price, p.id))
            if idx < len(self._products_by_price) and self._products_by_price[idx][1] == p.id:
                self._products_by_price.pop(idx)  # O(n) worst case shift

    def products_in_price_range(self, lo: float, hi: float) -> list[Product]:
        """O(log n) to locate the range boundaries + O(k) to collect matches."""
        start = bisect.bisect_left(self._products_by_price, (lo, ""))
        end = bisect.bisect_right(self._products_by_price, (hi, chr(0x10FFFF)))
        return [self.products[pid] for _, pid in self._products_by_price[start:end]
                if pid in self.products]

    def all_products(self) -> list[Product]:
        return list(self.products.values())       # O(n)

    def vendor_products(self, vendor_id: str) -> list[Product]:
        return [p for p in self.products.values() if p.vendor_id == vendor_id]  # O(n)

    # ---------------- Orders ----------------
    def add_order(self, order: Order) -> None:
        self.orders[order.id] = order              # O(1)
        q = self._vendor_queues.setdefault(order.vendor_id, [])
        heapq.heappush(q, (order.created_at, order.id))  # O(log n)

    def next_pending_order_for_vendor(self, vendor_id: str) -> Optional[Order]:
        """Peek the oldest order for a vendor without scanning all orders. O(log n) amortized."""
        q = self._vendor_queues.get(vendor_id, [])
        while q:
            created_at, oid = q[0]
            order = self.orders.get(oid)
            if order is None or order.status == "delivered":
                heapq.heappop(q)   # O(log n), drop stale/completed entries
                continue
            return order
        return None

    def buyer_orders(self, buyer_id: str) -> list[Order]:
        return [o for o in self.orders.values() if o.buyer_id == buyer_id]  # O(n)

    def vendor_orders(self, vendor_id: str) -> list[Order]:
        return [o for o in self.orders.values() if o.vendor_id == vendor_id]  # O(n)

    def update_order_status(self, order_id: str, new_status: str) -> None:
        order = self.orders.get(order_id)          # O(1)
        if order:
            order.status = new_status
            order.history.append((new_status, time.time()))

    # ---------------- Reviews ----------------
    def add_review(self, review: Review) -> None:
        self.reviews.setdefault(review.product_id, []).append(review)  # O(1) amortized

    def product_rating(self, product_id: str) -> tuple[float, int]:
        revs = self.reviews.get(product_id, [])     # O(1) lookup, O(k) scan of that product's reviews
        if not revs:
            return 0.0, 0
        return round(sum(r.rating for r in revs) / len(revs), 2), len(revs)

    # ---------------- Audit log (OWASP A09) ----------------
    def log_action(self, actor_id: str, action: str, detail: str = "") -> None:
        self.audit_log.append({
            "actor_id": actor_id,
            "action": action,
            "detail": detail,
            "ts": time.time(),
        })


# A single process-wide store instance, imported by the UI layer.
STORE = DataStore()
