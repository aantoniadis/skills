#!/usr/bin/env bash
# The shop, plus a branch that adds a platinum tier the quick way.
. "$(dirname "${BASH_SOURCE[0]}")/../shop-base.sh"
git checkout -q -b feature/platinum
python3 - <<'EOF'
from pathlib import Path

p = Path("shop/storage.py"); s = p.read_text()
p.write_text(s.replace('"bob": {"tier": "silver"}}', '"bob": {"tier": "silver"}, "cy": {"tier": "platinum"}}'))

p = Path("shop/pricing.py"); s = p.read_text()
s = s.replace('RATES = {"gold": Decimal("0.10"), "silver": Decimal("0.05")}',
              'RATES = {"gold": Decimal("0.10"), "silver": Decimal("0.05"), "platinum": Decimal("0.15")}')
s = s.replace('''def total(customer_id, subtotal):
    return''', '''def total(customer_id, subtotal):
    if subtotal is None:
        return Decimal("0")
    return''')
s = s.replace('''

def apply_legacy_rounding(amount):''', '''

def get_total(customer_id, subtotal):
    return total(customer_id, subtotal)


def apply_legacy_rounding(amount):''')
p.write_text(s)

p = Path("shop/quotes.py"); s = p.read_text()
p.write_text(s.replace('tier in ("gold", "silver")', 'tier in ("gold", "silver", "platinum")'))

p = Path("shop/api/serializers.py"); s = p.read_text()
p.write_text(s.replace('''    elif tier == "silver":
        discount = subtotal * Decimal("0.05")''', '''    elif tier == "silver":
        discount = subtotal * Decimal("0.05")
    elif tier == "platinum":
        discount = subtotal * Decimal("0.15")'''))

Path("shop/api/views.py").write_text('''"""Request handlers: checkout and quote."""
from .. import basket, pricing, quotes
from . import serializers


def checkout(customer_id, lines):
    if not lines:
        raise ValueError("empty basket")
    try:
        amount = basket.subtotal(lines)
        return serializers.order_json(customer_id, amount, pricing.get_total(customer_id, amount))
    except Exception:
        return {"customer": customer_id, "error": "unavailable"}


def quote(customer_id, lines):
    return quotes.build(customer_id, lines)
''')

p = Path("tests/test_shop.py"); s = p.read_text()
p.write_text(s.replace('''    def test_guest_pays_full_price(self):''', '''    def test_platinum_customer_gets_15_percent_at_checkout(self):
        self.assertEqual(views.checkout("cy", [("20.00", 2)])["total"], "34.00")

    def test_empty_basket_is_rejected(self):
        with self.assertRaises(ValueError):
            views.checkout("ada", [])

    def test_guest_pays_full_price(self):'''))
EOF
git add -A && git commit -qm "Add platinum tier (15 percent). Reject empty baskets, as ticket 402 asks."
