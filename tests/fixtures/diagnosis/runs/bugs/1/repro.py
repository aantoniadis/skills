"""Reproduction loop: one stock timeout, then count reservations for the order (fictional example)."""
import sys


class StockStub:
    def __init__(self, timeouts):
        self.timeouts, self.rows = timeouts, []

    def reserve(self, order_id, quantity, key=None):  # records the row, then times out while replying
        if key is not None and any(r[2] == key for r in self.rows):
            return
        self.rows.append((order_id, quantity, key))
        if self.timeouts:
            self.timeouts -= 1
            raise TimeoutError("stock service timed out after recording the reservation")


def confirm(order_id, quantity, stock, with_key):
    for attempt in range(3):
        try:
            stock.reserve(order_id, quantity, key=order_id if with_key else None)
            break
        except TimeoutError:
            pass


stock = StockStub(timeouts=1)
confirm(42, 2, stock, with_key="--fixed" in sys.argv)
print(f"reservations={len(stock.rows)}")
