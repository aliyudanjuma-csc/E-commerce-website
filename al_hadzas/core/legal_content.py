"""
core/legal_content.py
-----------------------
Plain-text legal content shown on the Terms & Conditions, Privacy
Policy, and Return/Refund Policy pages. This is coursework-level
sample legal copy for demonstration purposes only and is NOT a
substitute for review by a qualified lawyer before any real launch
(see the Feasibility Study's Legal & Regulatory section).
"""

TERMS_AND_CONDITIONS = """AL-HADZAS COLLECTIONS - TERMS & CONDITIONS (Demo)

1. ACCEPTANCE OF TERMS
By creating an account or placing an order on AL-HADZAS COLLECTIONS, you agree to these
Terms & Conditions. If you do not agree, please do not use the platform.

2. WHO WE ARE
AL-HADZAS COLLECTIONS is a multi-vendor marketplace connecting independent African
tailors and designers ("Vendors") with buyers worldwide ("Buyers"). AL-HADZAS
facilitates listings, payments, and order tracking but does not manufacture the
garments sold on the platform.

3. ACCOUNTS
You must provide accurate information when registering and are responsible for
keeping your login credentials confidential. AL-HADZAS may suspend accounts that
violate these terms or show signs of fraudulent activity.

4. VENDOR OBLIGATIONS
Vendors must accurately describe products (fabric, origin, sizing), fulfil orders
within the stated timeframe, and maintain the quality standards reviewed during
vendor verification. AL-HADZAS reserves the right to remove listings or suspend
vendors who fail to meet these standards.

5. PRICING & PAYMENTS
All prices are shown in the platform's display currency. Payment is processed at
checkout; for Made-to-Measure orders, funds are held until the vendor confirms
shipment. AL-HADZAS charges vendors a commission per completed sale, disclosed in
the vendor dashboard.

6. INTELLECTUAL PROPERTY
Product photography, "Culture Notes" descriptions, and platform branding are the
property of AL-HADZAS COLLECTIONS or the respective vendor and may not be
reproduced without permission.

7. LIMITATION OF LIABILITY
AL-HADZAS COLLECTIONS is a facilitator between Buyers and Vendors and is not liable
for delays, customs charges, or disputes arising from garment fit for
custom/made-to-measure items beyond the remedies described in the Return & Refund
Policy.

8. GOVERNING LAW
These terms are governed by the laws of the jurisdiction in which AL-HADZAS
COLLECTIONS is formally registered (to be finalized prior to real-world launch).

9. CHANGES TO THESE TERMS
AL-HADZAS may update these Terms & Conditions from time to time; continued use of
the platform after changes constitutes acceptance of the revised terms.
"""

PRIVACY_POLICY = """AL-HADZAS COLLECTIONS - PRIVACY POLICY (Demo)

1. INFORMATION WE COLLECT
- Account data: name, email, password (stored as a salted hash, never in plain
  text), and role (buyer/vendor).
- Order data: shipping address, order items, and order status history.
- Vendor data: business name, country, verification documents (verification flow
  simulated for coursework purposes).
- We do NOT collect or store raw payment card data - checkout in this build is a
  simulated sandbox flow.

2. HOW WE USE YOUR INFORMATION
We use collected data to operate your account, process and track orders, verify
vendors, personalize product recommendations via on-platform semantic search, and
improve the CRM chatbot's answers.

3. DATA SHARING
We share the minimum necessary order/shipping information with the relevant
Vendor to fulfil your order. We do not sell personal data to third parties.

4. DATA RETENTION
Account and order data is retained for as long as your account is active plus a
reasonable period for dispute resolution, after which it may be anonymized or
deleted upon request.

5. YOUR RIGHTS (GDPR-ALIGNED)
Consistent with GDPR principles for EU/UK users, you may request access to,
correction of, or deletion of your personal data, and may withdraw consent for
non-essential processing at any time by contacting support.

6. SECURITY
Passwords are hashed with a per-user random salt using PBKDF2-HMAC-SHA256.
Sessions expire automatically after a period of inactivity. Uploaded files are
scanned before acceptance (see our security practices).

7. COOKIES / LOCAL STATE
This coursework build stores session state only in memory for the duration of
the demo session; no persistent tracking cookies are used.

8. CONTACT
For privacy questions in this coursework build, contact the project author
listed on the Idea & Validation report.
"""

RETURNS_POLICY = """AL-HADZAS COLLECTIONS - RETURN & REFUND POLICY (Demo)

1. READY-TO-WEAR ITEMS
Ready-to-wear garments may be returned within 14 days of delivery if unworn, with
tags attached, for a full refund minus the original shipping fee.

2. MADE-TO-MEASURE / CUSTOM ITEMS
Because Made-to-Measure garments are cut to your submitted measurements, they are
final sale except where the item:
   (a) arrives with a manufacturing defect, or
   (b) does not match the measurements you submitted at checkout.
In either case, contact support within 7 days of delivery with photos for review.

3. HOW TO START A RETURN
Open "My Orders", select the order, and choose "Request Return/Refund", or ask
the AL-HADZAS chatbot with your order id. A vendor or admin will review the
request within 3 business days.

4. REFUND TIMING
Approved refunds are released back to your original payment method. In this
coursework build, refund processing is simulated and reflected instantly in the
order status for demonstration purposes.

5. RETURN SHIPPING
For approved returns due to vendor error (wrong item, defect), AL-HADZAS covers
return shipping. For change-of-mind returns on eligible ready-to-wear items, the
buyer covers return shipping.

6. NON-RETURNABLE ITEMS
Altered, worn, or washed garments, and any item explicitly marked "Final Sale"
on the product page, are not eligible for return.
"""
