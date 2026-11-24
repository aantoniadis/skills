I found 11 candidates I could not contradict (C1–C11), and dropped 8 leads. C1–C8 and C11 ran at both base and head; C9 and C10 are inferred. This was one read of the consumer side only.

- **Pins:** base `016ab76`, head `1e70f7c`. Each probe ran with `PYTHONPATH` set to a disposable worktree of base or head, using the locked venv.
- **Where things are:** probes and `run_both.sh` are in `<scratch>/out-arm/find-bugs-fastapi-2/.scratch/router-tree/search-1/finder-consumers/probes/`. Every command and its full output are in `probes/results.txt` in that folder.
- **Rerunning:** I removed my worktrees afterwards and the checkout is unchanged. To rerun, recreate `finder-consumers/base` at 016ab76 and `finder-consumers/head` at 1e70f7c, then run `sh probes/run_both.sh <probe>`.

## Candidates

**C1. `scope["route"]` is the original route, without the include prefix or the include-level data**
- **Location:** `fastapi/routing.py` `_IncludedRouter._handle_selected` (`scope["route"] = original_route`), and `APIRoute.matches` (`child_scope["route"] = self`).
- **Trigger:** any request to a route from an included router, read through `request.scope["route"]` by a dependency or middleware.
- **Base:** `path='/items/{item_id}'`, `tags=['include-tag','route-tag']`, `unique_id='read_item_items__item_id__get'`.
- **Head:** `path='/{item_id}'`, `tags=['route-tag']`, `unique_id='read_item__item_id__get'`.
- **Contract broken:** `scope["route"]` used to describe the effective path operation. Code that keys on route path, tags or operation id now gets the unprefixed, partial view.
- **Probe:** `p1_scope_route.py`, executed.

**C2. Sentry transaction names collapse for included routers (a real consumer, installed in the venv)**
- **Location:** the same lines as C1. `sentry_sdk/integrations/fastapi.py:53-57` names the transaction from `request.scope["route"].path`.
- **Trigger:** two routers included with prefixes `/users` and `/items`, each with a `GET /` route.
- **Base:** transaction names `['/users/', '/items/']`.
- **Head:** `['/', '/']`. Every router's routes merge into the same transactions.
- **Probe:** `p2_sentry_txn.py`, executed, using a capturing transport with no network.

**C3. A user's `generate_unique_id_function` now receives an `_EffectiveRouteContext`, not the `APIRoute` (subclass)**
- **Location:** `_EffectiveRouteContext.from_api_route` calls `_populate_api_route_state`, which calls `current_generate_unique_id(route)` with that context.
- **Trigger:** a custom `route_class` that carries its own attribute, plus a `generate_unique_id_function` that reads it. This is the documented hook, and the docs annotate the argument as `route: APIRoute`.
- **Base:** receives `VersionedRoute`; the operation id is `v2_get_x`.
- **Head:** receives `_EffectiveRouteContext`, and the first request raises `AttributeError: '_EffectiveRouteContext' object has no attribute 'api_version'`. Candidates are built lazily on the first request, so the app fails on that request rather than at startup.
- **Probe:** `p3_unique_id_callback.py`, executed.

**C4. OpenAPI callbacks taken from a router that includes another router disappear**
- **Location:** `fastapi/openapi/utils.py` `get_openapi_path`. Its callback loop still has `if isinstance(callback, routing.APIRoute)`, so `_IncludedRouter` entries are skipped. `get_fields_from_routes` does traverse them, so their models are still collected.
- **Trigger:** `callbacks=callback_router.routes` where `callback_router.include_router(events_cb)`.
- **Base:** the operation has `callbacks: {'event_cb': {...}}`.
- **Head:** `callbacks: {}`, while the `Event` schema is still emitted.
- **Contract broken:** the callback docs this PR edits say "FastAPI will use those routes to generate the callback OpenAPI documentation."
- **Probe:** `p4_callbacks_nested.py`, executed.

**C5. An `app.openapi_schema` the user assigns is overwritten by the default `app.openapi()`**
- **Location:** `fastapi/applications.py` `openapi()`. `_openapi_routes_version` starts as `None`, so the first call always regenerates.
- **Trigger:** `app.openapi_schema = {...}` (loaded or pre-built), then `app.openapi()` or `/openapi.json`.
- **Base:** returns the assigned schema (title `custom`).
- **Head:** regenerates it (title `FastAPI`).
- **Probe:** `p5_preset_schema.py`, executed.

**C6. A parent `APIRouter` subclass's `add_api_route` override no longer runs for included routes**
- **Location:** `APIRouter.include_router`. Base re-added each route through `self.add_api_route(...)`; head appends an `_IncludedRouter` instead.
- **Trigger:** a parent router subclass whose `add_api_route` registers an extra no-slash path; a plain child router is included into it.
- **Base:** `GET /api/things` returns 200.
- **Head:** 404.
- **Probe:** `p6_subclass_overrides.py` part A, executed.

**C7. A route subclass that customises `self.dependant` or `self.app` in `__init__` loses that for included routes. This can be a security bypass.**
- **Location:** `_EffectiveRouteContext.from_api_route` rebuilds the dependant from the endpoint and dependencies. `APIRoute.handle` builds `request_response(self.get_route_handler())` and ignores `self.app`.
- **Trigger:** a `GuardedRoute` that inserts a guard dependency into `self.dependant` after `super().__init__`.
- **Base:** 403 (base re-ran the subclass `__init__` when including).
- **Head:** 200, and the endpoint runs without the guard.
- **Probe:** `p6_subclass_overrides.py` part B, executed.

**C8. A route subclass whose `get_route_handler` reads `self.dependant` directly skips include-level dependencies**
- **Location:** `APIRoute.get_route_handler`. The effective context reaches a subclass only through `super().get_route_handler()`, via a ContextVar; `self.*` still points at the original route.
- **Trigger:** `include_router(r, dependencies=[Depends(needs_token)])` with that subclass.
- **Base:** 401.
- **Head:** 200. Router-level auth is silently skipped.
- **Probe:** `p6_subclass_overrides.py` part C, executed.

**C9. `get_route_handler()` now runs on every request for included routes**
- **Location:** `APIRoute.handle`.
- **Trigger:** five requests to an included route that uses a counting subclass.
- **Base:** 0 calls (built once when the route is created).
- **Head:** 5 calls.
- **Contracts broken:** the bigger-applications doc at head says routing "is designed to be lightweight and to avoid adding overhead to each request". Subclass side effects in `get_route_handler` now repeat per request.
- **Probe:** `p6_subclass_overrides.py` part D, executed. The per-request cost itself is *inferred*; a timing comparison would settle it.

**C10. `app.routes` consumers: `.path` fails, and the old documented `operation_id` rewrite silently stops working**
- **Location:** `_IncludedRouter` has no `path` attribute and is not an `APIRoute`.
- **Base:** listing paths gives `[..., '/v1/items/{item_id}']`; the tutorial002 rewrite (from base docs) gives operationId `read_item`.
- **Head:** `AttributeError: '_IncludedRouter' object has no attribute 'path'`; the operationId stays `read_item_v1_items__item_id__get`, so generated client names change.
- **Other consumers:** the same pattern (iterate routes, call `.matches()`, read `.path`) is used by Sentry's Starlette integration (which falls back to the raw URL path) and, from memory and not verified here, by OpenTelemetry and prometheus instrumentators.
- **Intent:** the release notes declare this a breaking change, so it is "you decide".
- **Probe:** `p7_routes_iteration.py`, executed.

**C11. Docs and API declarations left stale**
- **Translated docs** (`docs/{de,es,fr,ja,ko,pt,ru,tr,uk,zh,zh-hant}/docs/advanced/path-operation-advanced-configuration.md:23`) still use `hl[2, 12:21, 24]` and still describe iterating `app.routes`. The rewritten `tutorial002_py310.py` is now 13 lines.
  - Base: correct.
  - Head: the highlight lines are out of range and the prose describes a removed pattern.
  - Inferred from `git grep`; a docs build would show it.
- **`get_openapi(routes=None)`** (the parameter is typed as required):
  - Base: returns a schema.
  - Head: `TypeError: 'NoneType' object is not iterable`.
  - `p8_misc.py`, executed.

## Dropped leads
- **Header-matching `APIRoute.matches` override on an included router:** same result at base and head (404 without the header, 200 with it). `p7`.
- **`request.url_for` from an included route:** same at base and head (`/v1/items/5`). `p7`.
- **Routes unhashable because `_IncludedRouter` is a dataclass:** base `Route` objects are already unhashable (`TypeError` at base too). `p7`.
- **Mutual include (A into B, B into A) now raises `AssertionError`:** this is a deliberate cycle guard. The live tree would otherwise loop forever. `p8`.
- **An empty-path route added after `include_router` without a prefix is not validated:** base did not include routes added later at all, so nothing regressed. `p8`.
- **`router.mount()` after include does not bump `_routes_version`, so the cached candidates go stale:** base never included Mounts from a sub-router, so this is a gap in a new feature, not a regression.
- **The docs' `generate_clients` `route.tags[0]` pattern:** the context's tags keep the base order (include tags first, then route tags).
- **Mutating the dict `app.openapi()` returns:** preserved until the routes change, which is the intended live behaviour. `p5` variant 2.