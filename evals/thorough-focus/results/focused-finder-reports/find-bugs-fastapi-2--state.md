I found six candidates in the state this change adds, from one read of base `016ab76` against head `1e70f7c`. Each one was run at both revisions. The checkout is unchanged, and the base and head worktrees I made are removed.

Every probe runs through `run.sh <probe>`, which runs it at base and then head. It uses `/tmp/real-pr-cache/fastapi/venv/bin/python` with `PYTHONPATH` set to each worktree. Probes, outputs and `COMMANDS.txt` are in `<scratch>/out-arm/find-bugs-fastapi-2/.scratch/router-tree/search-1/finder-state/probes/`.

## Candidates

**1. Two threads rebuilding a router's cached route list at once corrupt it** (executed)
- **Location:** `fastapi/routing.py`, `_IncludedRouter.effective_candidates` (head ~1431-1450). It replaces the list with `[]`, appends to `self._effective_candidates` one route at a time, and records the version number only at the end. There is no lock.
- **Trigger:** two threads reach an included router whose cache is cold or out of date at the same time. A realistic case is two sync endpoints calling `request.url_for` or `app.url_path_for` (or `app.openapi()`) for a nested router that no request has reached yet. A single async event loop cannot hit this, because the method never awaits.
- **Base:** not applicable. Routes are copied once, eagerly, by `include_router`.
- **Head, natural race:** in 39 of 40 trials (8 threads, 30 routes), the cached list held about 90 to 239 entries instead of 30. That stays until the next route change. `app.openapi()` then printed 206 "Duplicate Operation ID" warnings.
- **Head, forced interleaving:** thread A got back `['r1', 'r2']`, so route `r0` was missing. A third reader got the same short list while thread B was still building. The final cache was `['r1','r2','r0','r1','r2']`. A caller holding the short list gets a 404 or `NoMatchFound` for a route that exists.
- **Contract broken:** the route set must be the same whatever the timing, which the base guaranteed.
- **Probes:** `p4_candidates_race.py`, `p4c_first_route_lookup.py`, `p4b_forced_interleaving.py`, with results in `results-p4*.txt`.

**2. `app.openapi()` overwrites a schema the user assigned** (executed)
- **Location:** `fastapi/applications.py:1083-1101`. The new condition `self._openapi_routes_version != routes_version` is always true on the first call, because the stored version starts as `None`.
- **Trigger:** `app.openapi_schema = {...}` is set before the first `app.openapi()` call or the first `GET /openapi.json`.
- **Base:** the assigned schema is returned (title "CUSTOM").
- **Head:** a regenerated schema is returned (title "FastAPI").
- **Related:** in-place edits to a generated schema, such as adding `x-logo` to `info`, are silently dropped once any route is added later. At base, the edits were kept, although the late route was also missing from the schema.
- **Contract broken:** `app.openapi_schema` worked as a user-settable cache, and the method's own text describes it as a cached schema.
- **Probe:** `p1_openapi_preset.py`, result in `results-p1-p3.txt`.

**3. Building the route list on first use moves `include_router` validation errors to request time** (executed)
- **Location:** `_RouterIncludeContext` / `_EffectiveRouteContext.from_api_route` → `_populate_api_route_state` asserts, run lazily from `effective_candidates`.
- **Trigger:** `app.include_router(router, responses={204: {"model": M}})`, or any include-level argument that the route-state checks reject.
- **Base:** `include_router` raises `AssertionError: Status code 204 must not have a response body` while the app starts.
- **Head:** `include_router` succeeds. Every request to that router returns 500, and `app.openapi()` raises. The failed build never stores a version, so it repeats the same failure on every request.
- **Contract broken:** a bad configuration should fail when the app starts, not on every request.
- **Probe:** `p3_deferred_assert.py`, result in `results-p1-p3.txt`.

**4. Routes added through Starlette's methods after the first request are never seen** (executed)
- **Location:** `APIRouter._routes_version` is bumped only by `add_route`, `add_websocket_route`, `add_api_route`, `add_api_websocket_route` and `include_router`. Starlette's `Router.mount`, `Router.host` and a direct `router.routes.append` don't change it. `_IncludedRouter.effective_candidates` then keeps serving its stale cache.
- **Trigger:** on an included router, call `router.mount(...)` or `router.routes.append(Route(...))` after a request has already reached it.
- **Base:** 404 in both orders, because Mount and late routes were never copied.
- **Head:** 200 if added before the first request, 404 if added after.
- **Contract broken:** the change's release notes say "Adding routes after a router is included now works". Here the result depends on request timing. Mount support inside included routers is new in this change, so this is not a regression from base. It is inconsistent behaviour of the new feature.
- **Probe:** `p2_mount_after_first_request.py`, result in `results-p1-p3.txt`.

**5. Per-request routing cost grows with nesting depth** (executed)
- **Cause:** nothing is cached per request. On every request:
  - `_get_routes_version()` walks the whole subtree at each nesting level.
  - `_IncludedRouter._match` runs twice, once in `matches` and once in `_handle_selected`.
  - `APIRoute.handle` rebuilds `request_response(self.get_route_handler())`.
- **Trigger:** routers nested 4 deep with 50 routes each, requesting the last route.
- **Base:** 299 µs per request (140 µs at depth 1).
- **Head:** 920 µs per request (255 µs at depth 1), with 30 `_get_routes_version` calls per request.
- **Contract:** none explicit. How much this matters depends on the app's route count and nesting depth.
- **Probe:** `p5_per_request_cost.py`, result in `results-p5.txt`.

**6. The previously documented "route names as operationIds" pattern silently stops working for included routes** (executed)
- **Trigger:** `for r in app.routes: if isinstance(r, APIRoute): r.operation_id = r.name`, run on an app that uses `include_router`.
- **Base:** operationId is `read_items`.
- **Head:** operationId is `read_items_api_items_get`. `app.routes` now holds `_IncludedRouter` entries, so the loop skips those routes.
- **Contract:** the release notes declare this as a breaking change and the docs were rewritten, so this is a decision for the author rather than a clear defect.
- **Probe:** `p6_mutate_route_after_include.py` part (a), result in `results-p6.txt`.

## Dropped leads
- **Collisions in the summed version counter:** counters only increase, so any add raises the sum. Equal sums need routes to be removed, which no code path tracks.
- **Wrong recursion in a diamond include** (`seen` in `_get_routes_version`): a router reached twice still adds its own counter, so the sum still only increases.
- **`_effective_route_context_var` leaking between requests:** it is set and reset synchronously around `get_route_handler`, and a ContextVar is private to each task.
- **Stale keys left in `scope["fastapi"]` after `_handle_selected`:** the scope belongs to one request, and every reader checks `original_route is self` / `original_router is self` by identity.
- **Two threads regenerating `openapi()` at once:** both build the same schema, and the last write wins. Harmless.
- **Editing a sub-router's route attribute after include:** `p6` part (b) shows the change doesn't reach the schema at base or head. That predates this change.
- **`on_startup` handlers and lifespan added to a sub-router after include are not propagated:** they are copied once at include time, the same as base.