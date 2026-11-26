#!/usr/bin/env bash
# A parcel depot in Ruby. On main, one delivery method holds its own rules. The branch moves those
# rules into a shared module and adds one module for each new kind; the new modules hold only a constant.
# It also adds an option nothing sets, a price cache with no rule for when it is stale, a guard with no producer,
# and a dependency of the delivery rules on the rates, which already depend on them.
set -euo pipefail
export GIT_AUTHOR_NAME=eval GIT_AUTHOR_EMAIL=eval@example.invalid GIT_COMMITTER_NAME=eval GIT_COMMITTER_EMAIL=eval@example.invalid
git init -q -b main
mkdir -p lib/depot/delivery test
printf '/.scratch/\n' > .gitignore
printf '# depot\n\nPrices, labels, and delivery promises for parcels.\n\nRun tests: `ruby -Ilib test/test_depot.rb`\n' > README.md
cat > lib/depot.rb <<'EOF'
require_relative "locker"
require_relative "depot/delivery/standard"
require_relative "depot/rates"
require_relative "depot/labels"
require_relative "depot/checkout"
EOF
cat > lib/locker.rb <<'EOF'
# A parcel locker at a station: a model, stored by the stations service.
class Locker
  attr_reader :id, :free_slots

  def initialize(id, free_slots)
    @id = id
    @free_slots = free_slots
  end

  def full? = free_slots.zero?
end
EOF
cat > lib/depot/delivery/standard.rb <<'EOF'
module Depot
  module Delivery
    # Standard delivery: every rule about an order's delivery block.
    module Standard
      KIND = "standard"

      # The delivery block of a standard order, or nil.
      def self.config(order)
        block = order[:delivery]
        block if block && block[:kind].to_s == KIND
      end

      def self.tracked?(order)
        block = order[:delivery]
        !block.nil? && block[:tracking] != false
      end

      def self.zone(order)
        block = order[:delivery]
        block && block[:postcode].to_s[0, 2]
      end

      def self.days(order)
        block = order[:delivery]
        block ? block.fetch(:days, 3) : nil
      end
    end
  end
end
EOF
cat > lib/depot/rates.rb <<'EOF'
module Depot
  # What a delivery costs. One resolver for each kind of delivery.
  module Rates
    class StandardRate
      def handles?(order) = !Delivery::Standard.config(order).nil?

      def price(order) = order[:weight_kg] <= 2 ? 4.90 : 7.90
    end

    RESOLVERS = [StandardRate].freeze

    def self.for(order)
      resolver = RESOLVERS.map(&:new).find { _1.handles?(order) }
      raise ArgumentError, "no rate for this delivery" unless resolver

      resolver.price(order)
    end
  end
end
EOF
cat > lib/depot/labels.rb <<'EOF'
module Depot
  # The text printed on a parcel label.
  module Labels
    def self.text(order)
      zone = Delivery::Standard.zone(order)
      tracked = Delivery::Standard.tracked?(order) ? "TRACKED" : "UNTRACKED"
      "#{order[:delivery][:kind].upcase} #{zone} #{tracked}"
    end
  end
end
EOF
cat > lib/depot/checkout.rb <<'EOF'
module Depot
  module Checkout
    def self.summary(order)
      { price: Rates.for(order), promise_days: Delivery::Standard.days(order), label: Labels.text(order) }
    end
  end
end
EOF
cat > test/test_depot.rb <<'EOF'
require "minitest/autorun"
require "depot"

class DepotTest < Minitest::Test
  STANDARD = { weight_kg: 1, delivery: { kind: "standard", postcode: "10435" } }.freeze

  def test_standard_config_is_the_delivery_block
    assert_equal "10435", Depot::Delivery::Standard.config(STANDARD)[:postcode]
    assert_nil Depot::Delivery::Standard.config({ delivery: { kind: "other" } })
  end

  def test_standard_rules
    assert Depot::Delivery::Standard.tracked?(STANDARD)
    assert_equal "10", Depot::Delivery::Standard.zone(STANDARD)
    assert_equal 3, Depot::Delivery::Standard.days(STANDARD)
  end

  def test_checkout_summary
    assert_equal({ price: 4.90, promise_days: 3, label: "STANDARD 10 TRACKED" }, Depot::Checkout.summary(STANDARD))
  end
end
EOF
git add -A && git commit -qm "Depot: standard delivery, rates, labels, checkout"

git checkout -q -b feature/delivery-kinds
cat > lib/depot.rb <<'EOF'
require_relative "locker"
require_relative "depot/delivery/base"
require_relative "depot/delivery/standard"
require_relative "depot/delivery/express"
require_relative "depot/delivery/locker"
require_relative "depot/rates"
require_relative "depot/labels"
require_relative "depot/checkout"
EOF
cat > lib/depot/delivery/base.rb <<'EOF'
module Depot
  module Delivery
    # Every rule about an order's delivery block. A kind module extends this and names its KIND.
    module Base
      extend self

      def self.modules = [Standard, Express, Locker]
      def self.kinds = modules.map { _1::KIND }
      def self.block(order) = order[:delivery]

      # The delivery block of an order of this kind, or nil.
      def config(order)
        block = Base.block(order)
        block if block && block[:kind].to_s == self::KIND
      end

      def tracked?(order)
        block = Base.block(order)
        !block.nil? && block[:tracking] != false
      end

      def zone(order)
        block = Base.block(order)
        block && block[:postcode].to_s[0, 2]
      end

      def days(order)
        block = Base.block(order)
        block ? block.fetch(:days) { Rates.for(order) > 9 ? 1 : 3 } : nil
      end
    end
  end
end
EOF
cat > lib/depot/delivery/standard.rb <<'EOF'
module Depot
  module Delivery
    module Standard
      extend Base
      KIND = "standard"
    end
  end
end
EOF
cat > lib/depot/delivery/express.rb <<'EOF'
module Depot
  module Delivery
    module Express
      extend Base
      KIND = "express"
    end
  end
end
EOF
cat > lib/depot/delivery/locker.rb <<'EOF'
module Depot
  module Delivery
    module Locker
      extend Base
      KIND = "locker"
    end
  end
end
EOF
cat > lib/depot/rates.rb <<'EOF'
module Depot
  # What a delivery costs. One resolver for each kind of delivery.
  module Rates
    class StandardRate
      def handles?(order) = !Delivery::Standard.config(order).nil?

      def price(order) = order[:weight_kg] <= 2 ? 4.90 : 7.90
    end

    class ExpressRate
      def handles?(order) = !Delivery::Express.config(order).nil?

      def price(order) = 9.90 + (order[:weight_kg] > 2 ? 5.00 : 0)
    end

    class LockerRate
      def handles?(order) = !Delivery::Locker.config(order).nil?

      def price(order) = 3.50
    end

    RESOLVERS = [StandardRate, ExpressRate, LockerRate].freeze

    def self.for(order)
      @prices ||= {}
      @prices[order[:id]] ||= begin
        resolver = RESOLVERS.map(&:new).find { _1.handles?(order) }
        raise ArgumentError, "no rate for this delivery" unless resolver

        resolver.price(order)
      end
    end
  end
end
EOF
cat > lib/depot/labels.rb <<'EOF'
module Depot
  # The text printed on a parcel label.
  module Labels
    KINDS = %w[standard express locker].freeze

    def self.text(order, compact: false)
      kind = order[:delivery][:kind].to_s
      raise ArgumentError, "unknown delivery kind" unless KINDS.include?(kind)

      zone = Delivery::Base.zone(order)
      return "#{kind[0].upcase}#{zone}" if compact

      tracked = Delivery::Base.tracked?(order) ? "TRACKED" : "UNTRACKED"
      "#{kind.upcase} #{zone} #{tracked}"
    end
  end
end
EOF
cat > lib/depot/checkout.rb <<'EOF'
module Depot
  module Checkout
    def self.summary(order)
      return nil if order.nil?

      { price: Rates.for(order), promise_days: Delivery::Base.days(order), label: Labels.text(order) }
    end
  end
end
EOF
python3 - <<'EOF'
from pathlib import Path
p = Path("test/test_depot.rb"); s = p.read_text()
s = s.replace('STANDARD = { weight_kg: 1,', 'STANDARD = { id: 1, weight_kg: 1,')
s = s.replace('''  def test_checkout_summary''', '''  def test_express_and_locker_orders
    express = { id: 2, weight_kg: 3, delivery: { kind: "express", postcode: "20095", days: 1 } }
    locker = { id: 3, weight_kg: 1, delivery: { kind: "locker", postcode: "80331", tracking: false } }
    assert_equal({ price: 14.90, promise_days: 1, label: "EXPRESS 20 TRACKED" }, Depot::Checkout.summary(express))
    assert_equal({ price: 3.50, promise_days: 3, label: "LOCKER 80 UNTRACKED" }, Depot::Checkout.summary(locker))
    assert_equal %w[standard express locker], Depot::Delivery::Base.kinds
  end

  def test_checkout_summary''')
p.write_text(s)
EOF
git add -A && git commit -qm "Delivery kinds: move the standard rules into a shared Base, add express and locker

The standard rules moved into Delivery::Base unchanged; Standard gives the same
results as before. Express and locker orders are requested in ticket 518.
Labels can print a compact form. Prices are cached per order. Checkout returns
nil for a nil order, for safety. An order with no promised days gets one day
when its price is above 9."
