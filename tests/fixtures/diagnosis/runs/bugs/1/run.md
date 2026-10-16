# Run record: confirmation retries reserve stock twice

Fictional example. Commit `ccccccc` of `acme/shop`, Python 3.12, no network, default configuration.

## Reproduction loop before the fix

```sh
python runs/bugs/1/repro.py
```

Output: `reservations=2` · three runs, same output, 0.4 s each.

## Regression test before the fix

```sh
pytest tests/test_confirm.py::test_confirm_reserves_once -q
```

Output: `FAILED tests/test_confirm.py::test_confirm_reserves_once - assert 2 == 1`

## Regression test after the fix

```sh
pytest tests/test_confirm.py -q
```

Output: `2 passed in 0.12s`

## Reproduction loop after the fix

```sh
python runs/bugs/1/repro.py --fixed
```

Output: `reservations=1`

## Consequence check, single attempt

```sh
python - <<'PY'
from runs.bugs.repro import StockStub, confirm
stock = StockStub(timeouts=0); confirm(42, 2, stock, with_key=True); print(len(stock.rows))
PY
```

Output: `1`

## Reach search

```sh
grep -rn "reserve(" orders/
```

Output: `orders/confirm.py:13` and `orders/cancel.py:11`; no other call sites.

## Bisection

```sh
git bisect start HEAD v2.3.0 && git bisect run python runs/bugs/1/repro.py
```

Output: `b7e1d2c is the first bad commit · Move stock client to gRPC (#980)`
