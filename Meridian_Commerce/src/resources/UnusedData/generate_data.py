import random
import csv
import datetime as dt
from pathlib import Path

random.seed(42)

OUT = Path("/home/claude/meridian_data/output")
OUT.mkdir(parents=True, exist_ok=True)

# ======================================================================
# Shared vocab
# ======================================================================

CATEGORIES = {
    "Electronics": ["Headphones", "Smartwatches", "Bluetooth Speakers", "Power Banks",
                    "Laptops", "Smartphones", "Tablets", "Cameras", "Chargers", "Earbuds"],
    "Footwear": ["Running Shoes", "Sneakers", "Formal Shoes", "Sandals", "Boots", "Loafers"],
    "Apparel": ["T-Shirts", "Jeans", "Jackets", "Dresses", "Activewear", "Sweaters"],
    "Home Goods": ["Blenders", "Air Fryers", "Cookware Sets", "Bedsheets", "Vacuum Cleaners",
                   "Lamps", "Storage Bins", "Coffee Makers"],
}

BRANDS = {
    "Electronics": ["Voltix", "Aurea", "Nexbyte", "Kinetix", "Pulseon"],
    "Footwear": ["Strydan", "Cliffwalk", "Nordrun", "Baseline", "Tersole"],
    "Apparel": ["Loomwear", "Urbanknit", "Fieldstitch", "Everly & Co", "Mono Studio"],
    "Home Goods": ["Havenly", "Kitchro", "Domicil", "Warmnest", "Clearview Home"],
}

ADJ = ["Everyday", "Pro", "Lite", "Max", "Essential", "Compact", "Premium", "Classic",
       "Urban", "Active", "Studio", "Signature"]

CITIES = ["Mumbai", "Bengaluru", "Delhi", "Pune", "Hyderabad", "Chennai", "Kolkata",
          "Ahmedabad", "Jaipur", "Lucknow", "Nagpur", "Indore", "Kochi", "Chandigarh"]

PAYMENT_METHODS = ["card", "UPI", "wallet", "COD", "netbanking"]

random_state = random.Random(7)

# ======================================================================
# 1. Product Catalog
# ======================================================================

products = []
product_id_counter = 1000

for category, sub_cats in CATEGORIES.items():
    for sub_category in sub_cats:
        n_products = random.randint(6, 9)
        for _ in range(n_products):
            product_id_counter += 1
            product_id = f"P{product_id_counter}"
            brand = random.choice(BRANDS[category])
            adj = random.choice(ADJ)
            base_name = sub_category[:-1] if sub_category.endswith("s") and sub_category not in ("Sneakers",) else sub_category
            product_name = f"{brand} {adj} {base_name}"
            sku = f"SKU-{category[:3].upper()}-{product_id_counter}"

            price_ranges = {
                "Electronics": (799, 45999),
                "Footwear": (699, 6999),
                "Apparel": (399, 4999),
                "Home Goods": (499, 12999),
            }
            lo, hi = price_ranges[category]
            price = round(random.uniform(lo, hi), 2)

            descriptions = {
                "Electronics": f"The {product_name} delivers reliable performance for daily use, "
                                f"with a {random.choice(['12-month', '18-month', '24-month'])} manufacturer warranty. "
                                f"Features {random.choice(['fast charging', 'long battery life', 'noise isolation', 'lightweight design', 'quick pairing'])} "
                                f"and is built for {random.choice(['travel', 'home use', 'work-from-home setups', 'daily commutes', 'outdoor use'])}.",
                "Footwear": f"{product_name} offers {random.choice(['cushioned', 'breathable', 'lightweight', 'all-day comfort'])} support, "
                            f"designed for {random.choice(['everyday wear', 'light workouts', 'office wear', 'casual outings'])}. "
                            f"Available in multiple sizes with a {random.choice(['rubber', 'EVA foam', 'memory foam'])} sole.",
                "Apparel": f"{product_name} is made from {random.choice(['100% cotton', 'a cotton-poly blend', 'breathable stretch fabric', 'soft brushed fleece'])}, "
                           f"ideal for {random.choice(['everyday wear', 'layering', 'casual outings', 'light workouts'])}. "
                           f"Machine washable and available in multiple sizes and colors.",
                "Home Goods": f"The {product_name} is built for {random.choice(['small kitchens', 'busy households', 'daily use', 'modern homes'])}, "
                              f"with {random.choice(['easy-clean surfaces', 'compact storage', 'energy-efficient operation', 'a durable build'])}. "
                              f"Comes with a {random.choice(['12-month', '18-month', '24-month'])} warranty on manufacturing defects.",
            }
            description = descriptions[category]

            stock_status = random.choices(["In Stock", "Out of Stock"], weights=[0.88, 0.12])[0]
            avg_rating = round(random.uniform(2.8, 4.9), 1)

            products.append({
                "product_id": product_id,
                "sku": sku,
                "product_name": product_name,
                "description": description,
                "category": category,
                "sub_category": sub_category,
                "brand": brand,
                "price": price,
                "stock_status": stock_status,
                "avg_rating": avg_rating,
            })

print(f"Generated {len(products)} products")

with open(OUT / "product_catalog.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(products[0].keys()))
    writer.writeheader()
    writer.writerows(products)

# ======================================================================
# 2. Orders & Returns
# ======================================================================

N_CUSTOMERS = 450
customer_ids = [f"C{2000 + i}" for i in range(N_CUSTOMERS)]

RETURN_REASONS_BY_CATEGORY = {
    "Electronics": ["Item stopped working after a few days", "Received a different model than ordered",
                    "Battery drains too quickly", "Item arrived with a cracked screen",
                    "Did not match product description", "Changed my mind after purchase"],
    "Footwear": ["Wrong size received", "Uncomfortable fit", "Material quality lower than expected",
                 "Color different from photos", "Sole started peeling within a week"],
    "Apparel": ["Wrong size ordered", "Fabric quality not as described", "Color faded after first wash",
                 "Item didn't fit as expected", "Changed my mind after purchase"],
    "Home Goods": ["Item arrived damaged", "Missing parts/accessories", "Doesn't work as advertised",
                   "Stopped working after light use", "Changed my mind after purchase"],
}

START_DATE = dt.date(2025, 1, 1)
END_DATE = dt.date(2026, 6, 30)
DATE_RANGE_DAYS = (END_DATE - START_DATE).days

orders = []
N_ORDERS = 1500

for i in range(N_ORDERS):
    order_id = f"O{10000 + i}"
    customer_id = random.choice(customer_ids)
    product = random.choice(products)
    product_id = product["product_id"]
    category = product["category"]

    discount_pct = random.choices([0, 5, 10, 15, 20, 25, 30], weights=[35, 15, 15, 12, 10, 8, 5])[0]
    price = round(product["price"] * (1 - discount_pct / 100), 2)

    order_date = START_DATE + dt.timedelta(days=random.randint(0, DATE_RANGE_DAYS))
    delivery_days = max(1, int(random.gauss(4.5, 2.2)))
    payment_method = random.choices(PAYMENT_METHODS, weights=[35, 30, 10, 20, 5])[0]

    # Return-risk logic: higher for high discount, long delivery, COD, certain categories
    base_risk = {"Electronics": 0.16, "Footwear": 0.14, "Apparel": 0.13, "Home Goods": 0.09}[category]
    risk = base_risk
    if discount_pct >= 20:
        risk += 0.06
    if delivery_days >= 8:
        risk += 0.07
    if payment_method == "COD":
        risk += 0.04
    if price > 15000:
        risk += 0.03
    risk = min(risk, 0.55)

    is_returned = 1 if random.random() < risk else 0
    return_reason = random.choice(RETURN_REASONS_BY_CATEGORY[category]) if is_returned else ""

    orders.append({
        "order_id": order_id,
        "customer_id": customer_id,
        "product_id": product_id,
        "category": category,
        "price": price,
        "discount_pct": discount_pct,
        "order_date": order_date.isoformat(),
        "delivery_days": delivery_days,
        "payment_method": payment_method,
        "is_returned": is_returned,
        "return_reason": return_reason,
    })

n_returned = sum(o["is_returned"] for o in orders)
print(f"Generated {len(orders)} orders, {n_returned} returned ({n_returned/len(orders):.1%})")

with open(OUT / "orders_returns.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(orders[0].keys()))
    writer.writeheader()
    writer.writerows(orders)

# ======================================================================
# 3. Customer Reviews
# ======================================================================

POSITIVE_PHRASES = [
    "Really happy with this purchase, works exactly as described.",
    "Great quality for the price, would buy again.",
    "Exceeded my expectations, arrived quickly too.",
    "Solid build quality and looks even better in person.",
    "Been using it for a few weeks now and no complaints at all.",
    "Perfect fit and the material feels premium.",
]
NEUTRAL_PHRASES = [
    "It's decent, does the job but nothing special.",
    "Average quality, matches the price point.",
    "Works fine so far, will update if anything changes.",
    "Good enough for occasional use.",
    "Not bad, but I expected slightly better finishing.",
]
NEGATIVE_PHRASES = [
    "Disappointed with the quality, expected better for this price.",
    "Stopped working within a week of regular use.",
    "Doesn't match the photos on the website at all.",
    "Sizing was off compared to the size chart.",
    "Packaging was poor and the item arrived slightly damaged.",
    "Not worth the money, wouldn't recommend.",
]

reviews = []
N_REVIEWS = 700
order_pool = orders  # reuse orders for realistic linkage

for i in range(N_REVIEWS):
    order = random.choice(order_pool)
    review_id = f"R{5000 + i}"
    product_id = order["product_id"]
    customer_id = order["customer_id"]

    if order["is_returned"]:
        star_rating = random.choices([1, 2, 3], weights=[45, 35, 20])[0]
    else:
        star_rating = random.choices([3, 4, 5], weights=[15, 35, 50])[0]

    if star_rating <= 2:
        review_text = random.choice(NEGATIVE_PHRASES)
    elif star_rating == 3:
        review_text = random.choice(NEUTRAL_PHRASES)
    else:
        review_text = random.choice(POSITIVE_PHRASES)

    order_date = dt.date.fromisoformat(order["order_date"])
    review_date = order_date + dt.timedelta(days=random.randint(3, 30))
    if review_date > END_DATE:
        review_date = END_DATE

    reviews.append({
        "review_id": review_id,
        "product_id": product_id,
        "customer_id": customer_id,
        "review_text": review_text,
        "star_rating": star_rating,
        "review_date": review_date.isoformat(),
    })

print(f"Generated {len(reviews)} reviews")

with open(OUT / "customer_reviews.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(reviews[0].keys()))
    writer.writeheader()
    writer.writerows(reviews)

# ======================================================================
# 4. Support Tickets / Conversations
# ======================================================================

TICKET_TEMPLATES = [
    ("order_status", "Where is my order? It was supposed to arrive by now and I haven't gotten any updates.", "medium"),
    ("order_status", "Can you tell me the current status of order {order_id}? Tracking hasn't updated in 3 days.", "medium"),
    ("return_request", "I want to return my order {order_id}, the item doesn't fit properly.", "medium"),
    ("return_request", "How do I initiate a return for {order_id}? It arrived damaged.", "high"),
    ("return_status", "I returned an item two weeks ago and still haven't received my refund. Order {order_id}.", "high"),
    ("warranty", "My product from order {order_id} stopped working, is it still under warranty?", "medium"),
    ("warranty", "I lost my invoice, can I still claim warranty on order {order_id}?", "low"),
    ("payment", "I was charged twice for order {order_id}, please refund the extra charge.", "high"),
    ("payment", "My payment failed but the amount was deducted from my account. Order {order_id} shows as unpaid.", "high"),
    ("product_question", "Does this product come in a larger size? I'm considering ordering it.", "low"),
    ("product_question", "Is the {product_hint} compatible with international chargers?", "low"),
    ("shipping", "Can I change the delivery address for order {order_id}? It hasn't shipped yet.", "medium"),
    ("shipping", "My order {order_id} shows delivered but I never received it.", "high"),
    ("complaint", "This is the third time I've contacted support about order {order_id} and no one has resolved it. Extremely frustrated.", "high"),
    ("general", "How do I use my loyalty points on my next purchase?", "low"),
]

CHANNELS = ["chat", "email", "phone-transcribed"]
STATUSES = ["Open", "Resolved", "Escalated"]

tickets = []
N_TICKETS = 400

for i in range(N_TICKETS):
    ticket_id = f"T{7000 + i}"
    customer_id = random.choice(customer_ids)
    category, template, urgency = random.choice(TICKET_TEMPLATES)

    has_order = "{order_id}" in template
    order_id = ""
    if has_order or random.random() < 0.4:
        order = random.choice(order_pool)
        order_id = order["order_id"]

    message_text = template.format(
        order_id=order_id if order_id else "my recent order",
        product_hint=random.choice(["headphones", "smartwatch", "blender", "running shoes"]),
    )

    channel = random.choices(CHANNELS, weights=[50, 35, 15])[0]
    order_date_for_ts = dt.date.fromisoformat(random.choice(order_pool)["order_date"])
    ts = dt.datetime.combine(order_date_for_ts, dt.time(random.randint(8, 21), random.randint(0, 59)))

    if urgency == "high":
        resolution_status = random.choices(STATUSES, weights=[25, 45, 30])[0]
    else:
        resolution_status = random.choices(STATUSES, weights=[20, 70, 10])[0]

    tickets.append({
        "ticket_id": ticket_id,
        "customer_id": customer_id,
        "order_id": order_id,
        "message_text": message_text,
        "channel": channel,
        "timestamp": ts.isoformat(sep=" "),
        "resolution_status": resolution_status,
    })

print(f"Generated {len(tickets)} tickets")

with open(OUT / "support_tickets.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(tickets[0].keys()))
    writer.writeheader()
    writer.writerows(tickets)

print("\nAll tabular datasets generated.")
