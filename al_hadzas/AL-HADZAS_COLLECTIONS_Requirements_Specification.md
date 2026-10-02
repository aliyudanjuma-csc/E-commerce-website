# AL-HADZAS COLLECTIONS
## Requirements Elicitation & Specification
**Prepared for:** MSc Computer Science Coursework — E-Commerce Website Development
**Prepared by:** [Your Name]
**Date:** September 2026

---

## 1. Purpose

This document describes how requirements for AL-HADZAS COLLECTIONS were elicited, and specifies the resulting **functional requirements (FRs)**, **non-functional requirements (NFRs)**, and **system requirements** that will guide design and implementation.

---

## 2. Requirements Elicitation

### 2.1 Elicitation Techniques Used

| Technique | How It Was Applied | Key Outputs |
|---|---|---|
| **Stakeholder interviews** | 5–8 informal interviews with target buyers (diaspora/international fashion consumers) and 2–3 African tailors/designers | Pain points: sizing uncertainty, trust in prepaying, delivery delays, lack of cultural context in listings |
| **Online survey (Google Forms)** | 50–100 respondents from diaspora/African student networks | Willingness-to-pay data, preferred garment categories, top trust concerns |
| **Competitor analysis / teardown** | Screen walkthroughs of Afrikrea, Fashtracker, KIKI Clothing, Etsy African sellers | Feature benchmarks: sizing guides, vendor verification badges, checkout flow, review systems |
| **Document/market research review** | Secondary sources (IMARC, African Business, TechCabal) | Confirmed market size, growth rate, and that demand skews international rather than domestic |
| **Persona & user story workshops (self-conducted)** | Drafted personas (diaspora professional, culture enthusiast, event buyer, tailor/vendor) and wrote user stories from each perspective | Basis for functional requirement statements below |
| **Prototyping / low-fidelity wireframes** | Sketches of homepage, product page, checkout, vendor dashboard reviewed informally with 3–4 peers | Early UX feedback folded into NFRs (usability) |

### 2.2 Stakeholders Identified

- **Buyers** — diaspora consumers, global fashion enthusiasts, event-driven shoppers
- **Vendors** — independent tailors, small African fashion houses
- **Platform admin** — verifies vendors, moderates catalogue, resolves disputes
- **Payment/logistics partners** — Stripe/Paystack (payments), courier partners (e.g., DHL) — external actors, not direct users
- **Course evaluator** — assesses the coursework deliverable against academic criteria

### 2.3 Sample User Stories (elicitation artifact)

- *As a diaspora buyer, I want to filter garments by country of origin and occasion, so I can quickly find culturally relevant attire for an event.*
- *As a buyer, I want a standardized sizing guide with measurement instructions, so I can order made-to-measure clothing with confidence.*
- *As a vendor, I want a simple dashboard to upload products and view orders, so I don't need technical skills to sell internationally.*
- *As a buyer, I want to see vendor verification badges and reviews, so I can trust a seller before prepaying.*
- *As an admin, I want to approve/reject new vendor applications, so the catalogue maintains quality and authenticity.*

---

## 3. Functional Requirements (FR)

Functional requirements describe *what the system must do*.

| ID | Requirement | Priority | Source |
|---|---|---|---|
| FR-01 | The system shall allow users to register and log in as either a Buyer or a Vendor. | Must | User stories, interviews |
| FR-02 | The system shall allow buyers to browse products filtered by country of origin, fabric type, occasion, and size. | Must | Survey, competitor analysis |
| FR-03 | The system shall display a product detail page including images, price, fabric description, "Culture Notes," and a sizing guide. | Must | Interviews (sizing/trust concerns) |
| FR-04 | The system shall allow buyers to add products to a cart and proceed to checkout. | Must | Core e-commerce requirement |
| FR-05 | The system shall integrate a sandbox/test payment gateway (e.g., Stripe/Paystack) to process checkout. | Must | Technical feasibility study |
| FR-06 | The system shall allow vendors to create, edit, and remove product listings via a vendor dashboard. | Must | Vendor user stories |
| FR-07 | The system shall allow vendors to view and update the status of received orders (placed → processing → shipped → delivered). | Must | Operational feasibility |
| FR-08 | The system shall allow an admin to review and approve/reject new vendor applications. | Must | Trust/vetting requirement from interviews |
| FR-09 | The system shall allow buyers to leave a rating and written review for a purchased product/vendor. | Should | Competitor benchmark (trust signals) |
| FR-10 | The system shall send order confirmation notifications (on-screen and/or email) after checkout. | Should | Standard e-commerce expectation |
| FR-11 | The system shall allow buyers to track the status of their order. | Should | Buyer trust/interview feedback |
| FR-12 | The system shall allow admin to moderate/remove flagged product listings or reviews. | Could | Platform integrity |
| FR-13 | The system shall support a "Made-to-Measure" order option where buyers submit custom measurements. | Could | Vendor differentiation strategy |
| FR-14 | The system shall allow currency display conversion for international buyers (display only, not live rates, for MVP). | Could | Global buyer persona needs |

*(Priority uses MoSCoW: Must / Should / Could / Won't-for-MVP.)*

---

## 4. Non-Functional Requirements (NFR)

Non-functional requirements describe *how well* the system performs its functions — quality attributes rather than features.

| ID | Category | Requirement |
|---|---|---|
| NFR-01 | **Usability** | A first-time buyer shall be able to complete a mock checkout without external help in a usability test, with ≥3 of 5 test users succeeding unaided (per feasibility study success metric). |
| NFR-02 | **Performance** | Product listing pages shall load within 3 seconds under normal conditions on a standard broadband/mobile connection. |
| NFR-03 | **Availability** | The system shall target 99% uptime during the coursework demo/evaluation period (excluding planned maintenance). |
| NFR-04 | **Security** | User passwords shall be stored using industry-standard hashing (e.g., bcrypt); all payment data shall be handled only via the third-party gateway's PCI-compliant sandbox, never stored directly on AL-HADZAS servers. |
| NFR-05 | **Data Protection / Privacy** | The system shall include a privacy policy and only collect data necessary for account creation and order fulfillment, in line with GDPR principles for EU/UK users. |
| NFR-06 | **Scalability** | The system architecture shall support horizontal scaling (e.g., stateless backend services) so that vendor/product growth does not require a redesign. |
| NFR-07 | **Compatibility** | The website shall render correctly on the latest two versions of Chrome, Safari, and Firefox, and shall be responsive across desktop, tablet, and mobile screen sizes. |
| NFR-08 | **Accessibility** | Core pages (homepage, product page, checkout) shall meet WCAG 2.1 AA basics (alt text on images, sufficient color contrast, keyboard navigability). |
| NFR-09 | **Maintainability** | Code shall follow a documented style guide and modular architecture (e.g., separated frontend/backend/services) to allow a new developer to onboard within one week. |
| NFR-10 | **Localization readiness** | The system shall be structured to support future multi-currency and multi-language support, even if only English/one currency ships in the MVP. |
| NFR-11 | **Reliability** | Checkout transactions shall be atomic — a failed payment shall not create a confirmed order record. |
| NFR-12 | **Auditability** | All vendor approval/rejection actions by admin shall be logged with timestamp and admin ID for accountability. |

---

## 5. System Requirements

System requirements define the technical environment needed to build, run, and support the platform.

### 5.1 Software Requirements

| Component | Requirement |
|---|---|
| Frontend | React.js / Next.js (or equivalent modern JS framework), HTML5, CSS3 (Tailwind or similar) |
| Backend | Node.js (Express) or Python (Django/FastAPI) |
| Database | PostgreSQL (relational data: users, orders, products, vendors) |
| Payment Gateway | Stripe or Paystack (sandbox/test mode for coursework) |
| Authentication | JWT-based session management or OAuth2 (e.g., via Auth0/Firebase Auth for coursework simplicity) |
| Hosting/Deployment | Vercel/Netlify (frontend), Render/Railway (backend), or a single full-stack host (e.g., Heroku free tier equivalent) |
| Version Control | Git + GitHub for source control and collaboration |
| Testing Tools | Jest/PyTest for unit tests; Postman for API testing; Lighthouse for performance/accessibility audits |

### 5.2 Hardware Requirements (Development Environment)

| Item | Minimum Spec |
|---|---|
| Development machine | 8GB RAM, quad-core CPU, 20GB free storage |
| Internet connection | Stable broadband (for cloud services, package installs, deployment) |
| Testing devices | At least one desktop browser + one mobile device (or emulator) for responsive testing |

### 5.3 Operational/Environmental Requirements

- A registered domain name (or subdomain) for demo deployment.
- SSL/TLS certificate (typically provided free by hosting platforms like Vercel/Render) for HTTPS.
- Sandbox/test credentials for the chosen payment gateway.
- A seeded test dataset (mock vendors, products, orders) to demonstrate full functionality during evaluation.

---

## 6. Traceability Note

Each functional and non-functional requirement above traces back to either: (a) a documented pain point from stakeholder interviews/survey, (b) a feature validated by competitor benchmarking, or (c) a constraint identified in the Feasibility Study. This ensures the coursework build is not feature-creeping beyond what was actually validated in the Idea & Validation and Feasibility Study documents.
