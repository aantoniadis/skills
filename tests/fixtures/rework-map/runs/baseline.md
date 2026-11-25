# Baseline run

Fictional record for the rework-map fixture.

- Command: `python -m pytest tests/pricing -q --cov=shop/pricing --cov-context=test`
- Revision: `dddddddddddddddddddddddddddddddddddddddd` of the fictional `acme/shop`, no local changes.
- Result: 42 passed in 3.1 s.
- Coverage: 91% of `shop/pricing`, 64% of `shop/api/serializers.py`.

## Probes

- `runs/probe_loyalty.py`: a gold customer with a 40.00 basket through `POST /checkout` and through `POST /quotes`.
  Checkout total `36.00`; quote total `38.00`.
- Removal probe: `apply_legacy_rounding` deleted in a scratch worktree; 42 passed.
