#!/usr/bin/env bash
# A small Ruby order pipeline that passes one hash through every step and changes it on the way.
set -euo pipefail
export GIT_AUTHOR_NAME=eval GIT_AUTHOR_EMAIL=eval@example.invalid GIT_COMMITTER_NAME=eval GIT_COMMITTER_EMAIL=eval@example.invalid
git init -q -b main
mkdir -p lib/orders test docs
printf '/.scratch/\n' > .gitignore
cat > docs/design.md <<'EOF'
# Design

An order goes through four steps: intake, pricing, shipping, and the receipt.

- `Orders::Intake` is the only place that builds an order from request parameters,
  and the only place that checks them.
- After intake an order is not changed. Each later step reads the order and
  returns its own result.
- `Orders::Checkout` runs the steps in order. It keeps no state between requests.
EOF
cat > lib/orders.rb <<'EOF'
require_relative "orders/intake"
require_relative "orders/pricing"
require_relative "orders/shipping"
require_relative "orders/notifier"
require_relative "orders/checkout"
EOF
cat > lib/orders/intake.rb <<'EOF'
module Orders
  # Builds an order from request parameters.
  module Intake
    def self.build(params)
      lines = params["lines"]
      raise ArgumentError, "an order needs at least one line" if lines.nil? || lines.empty?
      { customer: { email: params["email"], tier: params["tier"] },
        lines: lines.map { |line| { price: line["price"].to_f, quantity: line["quantity"].to_i } } }
    end
  end
end
EOF
cat > lib/orders/pricing.rb <<'EOF'
module Orders
  module Pricing
    RATES = { "gold" => 0.10, "silver" => 0.05 }.freeze

    def self.total(order)
      subtotal = order[:lines].sum { |line| line[:price] * line[:quantity] }
      (subtotal * (1 - RATES.fetch(order[:customer][:tier], 0))).round(2)
    end
  end
end
EOF
cat > lib/orders/shipping.rb <<'EOF'
module Orders
  module Shipping
    def self.cost(order)
      Pricing.total(order) >= 50 ? 0.0 : 4.9
    end
  end
end
EOF
cat > lib/orders/notifier.rb <<'EOF'
module Orders
  module Notifier
    def self.receipt(order)
      "#{order[:customer][:email]}: #{format('%.2f', Pricing.total(order) + Shipping.cost(order))}"
    end
  end
end
EOF
cat > lib/orders/checkout.rb <<'EOF'
module Orders
  module Checkout
    def self.run(params)
      order = Intake.build(params)
      { total: Pricing.total(order), shipping: Shipping.cost(order), receipt: Notifier.receipt(order) }
    end
  end
end
EOF
cat > test/test_checkout.rb <<'EOF'
require "minitest/autorun"
require_relative "../lib/orders"

class CheckoutTest < Minitest::Test
  PARAMS = { "email" => "ada@example.invalid", "tier" => "gold", "lines" => [{ "price" => "20.00", "quantity" => "2" }] }.freeze

  def test_gold_customer_gets_ten_percent
    assert_equal 36.0, Orders::Checkout.run(PARAMS)[:total]
  end

  def test_an_order_needs_a_line
    assert_raises(ArgumentError) { Orders::Checkout.run("email" => "x", "lines" => []) }
  end
end
EOF
printf '# orders\n\nCheckout for a small shop. Design: [docs/design.md](docs/design.md).\n\nRun tests: `ruby test/test_checkout.rb`\n' > README.md
git add -A && git commit -qm "Orders: intake, pricing, shipping, receipt"

# Steps start writing their results into the order "so the next step does not recompute".
cat > lib/orders/pricing.rb <<'EOF'
module Orders
  module Pricing
    RATES = { "gold" => 0.10, "silver" => 0.05 }.freeze

    # Writes :discount and :total into the order.
    def self.apply!(order)
      return order if order[:lines].nil?
      subtotal = order[:total] || order[:lines].sum { |line| line[:price] * line[:quantity] }
      order[:discount] = (subtotal * RATES.fetch(order[:customer][:tier], 0)).round(2)
      order[:total] = (subtotal - order[:discount]).round(2)
      order
    end
  end
end
EOF
cat > lib/orders/shipping.rb <<'EOF'
module Orders
  module Shipping
    # Writes :shipping into the order and adds it to :total.
    def self.add!(order)
      order[:shipping] = order[:total] >= 50 ? 0.0 : 4.9
      order[:total] = (order[:total] + order[:shipping]).round(2)
      order
    end
  end
end
EOF
cat > lib/orders/notifier.rb <<'EOF'
module Orders
  module Notifier
    def self.receipt(order)
      currency = order.fetch(:currency, "EUR")
      "#{order.dig(:customer, :email)}: #{format('%.2f', order[:total])} #{currency} (saved #{order[:discount] || 0})"
    end
  end
end
EOF
cat > lib/orders/checkout.rb <<'EOF'
module Orders
  module Checkout
    def self.run(params)
      order = Intake.build(params)
      Pricing.apply!(order)
      Shipping.add!(order)
      order[:receipt] = Notifier.receipt(order)
      order
    end
  end
end
EOF
sed -i 's/assert_equal 36.0, Orders::Checkout.run(PARAMS)\[:total\]/assert_equal 40.9, Orders::Checkout.run(PARAMS)[:total]/' test/test_checkout.rb
git add -A && git commit -qm "Keep results in the order so later steps do not recompute"

# A report and a counter arrive; the last order is kept for resending a receipt.
cat > lib/orders/report.rb <<'EOF'
module Orders
  module Report
    @@totals = Hash.new(0)

    def self.record(order)
      currency = order.fetch(:currency, "USD")
      @@totals[currency] += order[:total]
      "#{order[:lines].size} lines, #{format('%.2f', order[:total])} #{currency}"
    end

    def self.totals
      @@totals
    end
  end
end
EOF
cat > lib/orders/checkout.rb <<'EOF'
module Orders
  module Checkout
    def self.run(params)
      order = Intake.build(params)
      Pricing.apply!(order)
      Shipping.add!(order)
      order[:receipt] = Notifier.receipt(order)
      order[:report] = Report.record(order)
      $last_order = order
      order
    end

    # Price an order again after its lines changed.
    def self.reprice(order)
      Pricing.apply!(order)
      Shipping.add!(order)
      order
    end
  end
end
EOF
cat >> lib/orders/notifier.rb <<'EOF'

module Orders
  module Notifier
    def self.resend
      receipt($last_order)
    end
  end
end
EOF
sed -i 's#require_relative "orders/notifier"#require_relative "orders/notifier"\nrequire_relative "orders/report"#' lib/orders.rb
cat >> test/test_checkout.rb <<'EOF'

class ReceiptTest < Minitest::Test
  def test_receipt_names_the_customer
    order = Orders::Checkout.run(CheckoutTest::PARAMS)
    assert_includes order[:receipt], "ada@example.invalid"
  end
end
EOF
git add -A && git commit -qm "Report per order, running totals, resend the last receipt, reprice"
sed -i 's/    # Writes :discount and :total into the order./    # Writes :discount and :total into the order. Safe to call when the order has no lines yet./' lib/orders/pricing.rb
sed -i 's/    # Writes :shipping into the order and adds it to :total./    # Writes :shipping into the order and adds it to :total. Free from 50./' lib/orders/shipping.rb
git add -A && git commit -qm "Comments on pricing and shipping"
