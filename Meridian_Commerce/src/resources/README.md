# Meridian Commerce — Capstone Datasets

Synthetic data generated to match the exact schemas in the capstone brief,
with shared IDs (`order_id`, `product_id`, `customer_id`) linking every file
into one coherent system, plus a fixed random seed so the data is
reproducible.

## Files

| File | Rows | Used in |
|------|------|---------|
| `orders_returns.csv` | 1,500 | Day 1 (primary), and as ground truth throughout |
| `product_catalog.csv` | 222 | Day 2, Day 6, Day 7 |
| `customer_reviews.csv` | 700 | Day 2, Day 3 |
| `support_tickets.csv` | 400 | Day 3, Day 4, Day 5 |
| `policy_return_refund.txt` | — | Day 6, Day 7 |
| `policy_shipping_delivery.txt` | — | Day 6, Day 7 |
| `policy_warranty.txt` | — | Day 6, Day 7 |
| `policy_payment_refunds_faq.txt` | — | Day 6, Day 7 |
| `policy_loyalty_program.txt` | — | Day 6, Day 7 |

## 1. orders_returns.csv

| Field | Notes |
|-------|-------|
| `order_id` | `O10000`-`O11499` |
| `customer_id` | `C2000`-`C2449` (450 unique customers, repeat buyers included) |
| `product_id` | links to `product_catalog.csv` |
| `category` | copied from the linked product at order time |
| `price` | post-discount order price |
| `discount_pct` | 0-30, skewed toward 0-10 |
| `order_date` | 2025-01-01 to 2026-06-30 |
| `delivery_days` | 1-15, roughly normal around 4-5 |
| `payment_method` | card / UPI / wallet / COD / netbanking |
| `is_returned` | target variable — **16.7% positive**, a realistic class imbalance for Day 1 |
| `return_reason` | free text, populated only when `is_returned == 1` |

**Built-in signal for Day 1 modeling:** return risk is higher for high
discount (≥20%), long delivery (≥8 days), COD payment, high price
(>₹15,000), and varies by category (Electronics/Footwear/Apparel higher
than Home Goods) — a genuine, learnable-but-not-trivial pattern rather than
random noise.

## 2. product_catalog.csv

| Field | Notes |
|-------|-------|
| `product_id` | `P1001`-`P1222` |
| `sku` | e.g. `SKU-ELE-1001` — distinct from `product_id`, deliberately included so Day 7's hybrid search (exact SKU lookup + semantic search) has a real reason to exist |
| `product_name` | e.g. "Voltix Signature Headphone" |
| `description` | 2-3 sentence free text — the field to embed in Day 2/7 |
| `category` / `sub_category` | Electronics, Footwear, Apparel, Home Goods, each with 6-10 sub-categories |
| `brand` | 5 brands per category |
| `price` | pre-discount catalog price |
| `stock_status` | In Stock / Out of Stock (~12% out of stock) |
| `avg_rating` | 2.8-4.9 |

## 3. customer_reviews.csv

| Field | Notes |
|-------|-------|
| `review_id` | `R5000`-`R5699` |
| `product_id` / `customer_id` | sampled from real orders, so review authorship is consistent with `orders_returns.csv` |
| `review_text` | short free text, sentiment matched to `star_rating` |
| `star_rating` | 1-5 — skewed lower for products from returned orders, higher otherwise, so sentiment signal is realistic rather than random |
| `review_date` | 3-30 days after the linked order date |

## 4. support_tickets.csv

| Field | Notes |
|-------|-------|
| `ticket_id` | `T7000`-`T7399` |
| `customer_id` | links to orders |
| `order_id` | populated for order-specific tickets, blank otherwise (~40% blank) |
| `message_text` | drawn from 15 realistic templates across order-status, return, warranty, payment, shipping, product-question, and complaint categories — useful for Day 3 zero/few-shot classification and Day 4 triage/urgency exercises |
| `channel` | chat / email / phone-transcribed |
| `timestamp` | datetime |
| `resolution_status` | Open / Resolved / Escalated, skewed toward Escalated for higher-urgency ticket types |

**Note:** `message_text` does not include an explicit category or urgency
label — that's intentional, since Day 3 and Day 4 have students classify
these themselves via prompting.

## 5. Policy & FAQ documents

Five long-form text documents written for Meridian Commerce, covering
return/refund, shipping/delivery, warranty, payment/refunds FAQ, and loyalty
program terms. These are the Day 6/7 RAG knowledge base. A few details are
worth knowing if you design retrieval exercises around them:

- The **return window differs by category** within `policy_return_refund.txt`
  (7/10/14 days depending on product type) — a good test of whether
  retrieval + generation handles category-specific clauses correctly rather
  than defaulting to "14 days" for everything.
- **Warranty vs. return window** are explicitly separate concepts in
  `policy_warranty.txt` — a common source of naive-RAG confusion worth
  probing.
- `policy_shipping_delivery.txt`'s delay-compensation clause and
  `policy_payment_refunds_faq.txt`'s duplicate-charge clause are both
  numeric-threshold rules (days / rupee amounts) — useful for testing
  whether generation reasons correctly over thresholds instead of just
  pattern-matching nearby text.

## Regenerating or extending the data

`generate_data.py` (included) regenerates the four CSVs from scratch with a
fixed seed (`random.seed(42)`). Adjust `N_ORDERS`, `N_REVIEWS`, `N_TICKETS`,
or the category/brand vocab lists near the top of the file to resize or
extend the dataset without breaking the ID linkage.
