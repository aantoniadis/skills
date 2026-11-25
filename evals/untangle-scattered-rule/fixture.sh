#!/usr/bin/env bash
# A small shop whose loyalty-discount rule drifted into three places over several commits.
set -euo pipefail
export GIT_AUTHOR_NAME=eval GIT_AUTHOR_EMAIL=eval@example.invalid GIT_COMMITTER_NAME=eval GIT_COMMITTER_EMAIL=eval@example.invalid
git init -q -b main
mkdir -p shop/api docs tests
printf '__pycache__/\n/.scratch/\n' > .gitignore
: > shop/__init__.py
: > shop/api/__init__.py
cat > docs/architecture.md <<'EOF'
# Architecture

The shop has three layers.

- `shop/api` translates requests and responses. It decides nothing about money.
- `shop/pricing.py` decides every price: discounts, totals, rounding.
- `shop/storage.py` is the only module that knows customer records.

Allowed dependencies: `api` uses `pricing` and `quotes`; `quotes` uses `pricing`;
`pricing` uses `storage`. Nothing else reads `storage`.
EOF
cat > shop/storage.py <<'EOF'
"""Customer records. The only module that knows how customers are stored."""
_CUSTOMERS = {"ada": {"tier": "gold"}, "bob": {"tier": "silver"}}


def tier_of(customer_id):
    record = _CUSTOMERS.get(customer_id)
    return record["tier"] if record else None
EOF
cat > shop/pricing.py <<'EOF'
"""Prices: the loyalty discount and the order total."""
from decimal import Decimal

from . import storage

RATES = {"gold": Decimal("0.05"), "silver": Decimal("0.05")}


def loyalty_discount(customer_id, subtotal):
    tier = storage.tier_of(customer_id)
    return subtotal * RATES.get(tier, Decimal("0"))


def total(customer_id, subtotal):
    return (subtotal - loyalty_discount(customer_id, subtotal)).quantize(Decimal("0.01"))
EOF
cat > shop/basket.py <<'EOF'
"""A basket is a list of (unit price, quantity) lines."""
from decimal import Decimal


def subtotal(lines):
    amount = Decimal("0")
    for price, quantity in lines:
        if quantity > 10000:
            quantity = 10000
        amount += Decimal(price) * quantity
    return amount
EOF
cat > shop/quotes.py <<'EOF'
"""A quote shows a customer what an order would cost."""
from . import basket, pricing


def build(customer_id, lines):
    amount = basket.subtotal(lines)
    return {"customer": customer_id, "total": str(pricing.total(customer_id, amount))}
EOF
cat > shop/api/views.py <<'EOF'
"""Request handlers: checkout and quote."""
from .. import basket, pricing, quotes
from . import serializers


def checkout(customer_id, lines):
    amount = basket.subtotal(lines)
    return serializers.order_json(customer_id, amount, pricing.total(customer_id, amount))


def quote(customer_id, lines):
    return quotes.build(customer_id, lines)
EOF
cat > shop/api/serializers.py <<'EOF'
"""Turn an order into the JSON the web client shows."""


def order_json(customer_id, subtotal, total):
    return {"customer": customer_id, "subtotal": str(subtotal), "total": str(total)}
EOF
cat > tests/test_shop.py <<'EOF'
import unittest

from shop.api import views


class CheckoutTest(unittest.TestCase):
    def test_gold_customer_gets_a_discount_at_checkout(self):
        self.assertEqual(views.checkout("ada", [("20.00", 2)])["total"], "38.00")

    def test_quote_has_a_total(self):
        self.assertIn("total", views.quote("bob", [("10.00", 1)]))


if __name__ == "__main__":
    unittest.main()
EOF
printf '# shop\n\nCheckout and quotes for a small shop. Design: [docs/architecture.md](docs/architecture.md).\n\nRun tests: `python3 -m unittest discover -s tests`\n' > README.md
git add -A && git commit -qm "Shop: checkout and quotes"

# The quote path gets its own copy of the discount, "to avoid a slow import".
python3 - <<'EOF'
from pathlib import Path
Path("shop/quotes.py").write_text('''"""A quote shows a customer what an order would cost."""
from decimal import Decimal

from . import basket, storage


def build(customer_id, lines):
    try:
        amount = basket.subtotal(lines)
        tier = storage.tier_of(customer_id)
        discount = amount * Decimal("0.05") if tier in ("gold", "silver") else Decimal("0")
        return {"customer": customer_id, "total": str((amount - discount).quantize(Decimal("0.01")))}
    except Exception:
        return {"customer": customer_id, "total": "0.00"}
''')
EOF
git add -A && git commit -qm "Quotes: compute the discount locally, never fail a quote"

# Guests check out: a deliberate rule, pinned by a test.
python3 - <<'EOF'
from pathlib import Path
p = Path("shop/pricing.py"); s = p.read_text()
s = s.replace('''    tier = storage.tier_of(customer_id)
    return subtotal * RATES.get(tier, Decimal("0"))''', '''    tier = storage.tier_of(customer_id)
    if tier is None:
        return Decimal("0")
    return subtotal * RATES.get(tier, Decimal("0"))''')
p.write_text(s)
p = Path("tests/test_shop.py"); s = p.read_text()
s = s.replace('''    def test_quote_has_a_total(self):''', '''    def test_guest_pays_full_price(self):
        self.assertEqual(views.checkout("guest-7", [("20.00", 2)])["total"], "40.00")

    def test_quote_has_a_total(self):''')
p.write_text(s)
EOF
git add -A && git commit -qm "Guest checkout: a customer with no tier pays full price (support ticket 311)"

# Gold goes to 10 percent in pricing; the quote copy is missed.
sed -i 's/RATES = {"gold": Decimal("0.05"), "silver": Decimal("0.05")}/RATES = {"gold": Decimal("0.10"), "silver": Decimal("0.05")}/' shop/pricing.py
sed -i 's/"38.00")/"36.00")/' tests/test_shop.py
git add -A && git commit -qm "Gold customers get 10 percent"

# The client wants to show the discount and free shipping: the serializer works both out itself.
cat > shop/api/serializers.py <<'EOF'
"""Turn an order into the JSON the web client shows."""
from decimal import Decimal

from .. import storage


def order_json(customer_id, subtotal, total):
    tier = storage.tier_of(customer_id)
    if tier == "gold":
        discount = subtotal * Decimal("0.10")
    elif tier == "silver":
        discount = subtotal * Decimal("0.05")
    else:
        discount = Decimal("0")
    shipping = Decimal("0") if subtotal >= 50 else Decimal("4.90")
    return {"customer": customer_id, "subtotal": str(subtotal), "discount": str(discount.quantize(Decimal("0.01"))),
            "shipping": str(shipping), "total": str(total)}
EOF
git add -A && git commit -qm "Show discount and shipping in the order JSON"

# A helper nobody calls, and one more touch of the two discount copies.
cat >> shop/pricing.py <<'EOF'


def apply_legacy_rounding(amount):
    """Round half down, as the old till did."""
    return amount.quantize(Decimal("0.01"), rounding="ROUND_HALF_DOWN")
EOF
sed -i 's/"""A quote shows a customer what an order would cost."""/"""A quote shows a customer what an order would cost, discount included."""/' shop/quotes.py
git add -A && git commit -qm "Pricing: legacy rounding helper; quotes docstring"
sed -i 's/"""Prices: the loyalty discount and the order total."""/"""Prices: the loyalty discount, the order total, and rounding."""/' shop/pricing.py
sed -i 's/discount included."""/loyalty discount included."""/' shop/quotes.py
git add -A && git commit -qm "Docstrings"
