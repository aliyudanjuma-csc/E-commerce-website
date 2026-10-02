"""
core/payment.py
------------------
Simulated (offline) payment processor. No real gateway is called --
this models the cost structure and control flow a real integration
(Stripe/Paystack) would have, so the checkout screen can show a
realistic, itemized "micro components" cost breakdown as required by
the brief, and so this module is a clean seam to swap in a real SDK
later without touching the UI layer.

Cost / micro-component model
-----------------------------
For an order subtotal S:
    commission_fee            = S * COMMISSION_RATE      (platform's cut of the vendor sale)
    payment_processing_fee    = S * CARD_FEE_RATE + CARD_FEE_FIXED  (mimics card-network fee structure)
    shipping_fee               = flat-rate by item count (simplified international shipping model)
    total                       = S + payment_processing_fee + shipping_fee
                                  (commission_fee is deducted from the vendor's payout, not
                                   added on top of what the buyer pays)

Complexity: O(m) in the number of items m in the cart (m << n, the
catalogue size), i.e. effectively O(1) per checkout relative to system size.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass

from core.data_store import OrderItem

COMMISSION_RATE = 0.18          # 18% platform commission on the vendor's sale
CARD_FEE_RATE = 0.029           # 2.9% card-processing fee (industry-typical)
CARD_FEE_FIXED = 0.30           # + $0.30 fixed fee per transaction
SHIPPING_FLAT_PER_ITEM = 6.50   # simplified consolidated international shipping model


@dataclass
class CostBreakdown:
    subtotal: float
    commission_fee: float
    payment_processing_fee: float
    shipping_fee: float
    total: float


def compute_cost_breakdown(items: list[OrderItem]) -> CostBreakdown:
    subtotal = round(sum(i.unit_price * i.quantity for i in items), 2)  # O(m)
    commission_fee = round(subtotal * COMMISSION_RATE, 2)
    processing_fee = round(subtotal * CARD_FEE_RATE + CARD_FEE_FIXED, 2)
    shipping_fee = round(SHIPPING_FLAT_PER_ITEM * sum(i.quantity for i in items), 2)
    total = round(subtotal + processing_fee + shipping_fee, 2)
    return CostBreakdown(subtotal, commission_fee, processing_fee, shipping_fee, total)


@dataclass
class PaymentResult:
    success: bool
    reference: str
    message: str


def process_payment(card_number: str, expiry: str, cvc: str, amount: float) -> PaymentResult:
    """Simulated gateway call. Performs only basic client-side shape
    validation (never real card verification) and always "succeeds"
    for well-formed input, to keep the coursework demo fully offline
    and deterministic. O(1)."""
    digits = card_number.replace(" ", "")
    if not (digits.isdigit() and 12 <= len(digits) <= 19):
        return PaymentResult(False, "", "Card number looks invalid.")
    if not re_expiry_ok(expiry):
        return PaymentResult(False, "", "Expiry must be in MM/YY format and in the future.")
    if not (cvc.isdigit() and 3 <= len(cvc) <= 4):
        return PaymentResult(False, "", "CVC looks invalid.")
    if amount <= 0:
        return PaymentResult(False, "", "Amount must be greater than zero.")

    reference = f"SIM-{int(time.time())}-{random.randint(1000, 9999)}"
    return PaymentResult(True, reference, "Payment authorized (simulated sandbox).")


def re_expiry_ok(expiry: str) -> bool:
    import re
    m = re.match(r"^(0[1-9]|1[0-2])/(\d{2})$", expiry.strip())
    if not m:
        return False
    month, yy = int(m.group(1)), int(m.group(2))
    year = 2000 + yy
    now = time.localtime()
    return (year, month) >= (now.tm_year, now.tm_mon)
