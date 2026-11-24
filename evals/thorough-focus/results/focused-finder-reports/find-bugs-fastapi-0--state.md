I found three candidates in the state this change adds that I could not contradict, and I confirmed all three by running probes at both head and base. This was one read, scoped to caches, lazy initialization, counters and long-lived containers. I did not run the static deltas, `weakened_checks.py` or the base tests, as you said the lead runs those.

Probes and their outputs are in `<scratch>/out-arm/find-bugs-fastapi-0/.scratch/router-tree/search-1/finder-state/probes/`, with the exact command in `COMMANDS.txt` and outputs in the `results*.txt` files. The base worktree has been removed and the checkout is unchanged.

## Candidates

**1. The included-router route cache is corrupted when threads build it at the same time (executed)**
- **Location:** `fastapi/routing.py`, `_IncludedRouter.effective_candidates()`.
  - It sets `self._effective_candidates = []`, then appends to `self._effective_candidates` (the shared attribute, not a local list), and sets the version only at the end.
  - It returns the shared attribute, not the list it built.
- **Trigger:** two or more threads reach a cold cache at once. The cache is cold on first use and after any route change. Ways to get there:
  - several `TestClient`s, each with its own event-loop thread;
  - sync endpoints in the threadpool calling `url_for` or `app.url_path_for` while the event loop matches requests;
  - free-threaded Python.
- **Head result:**
  - Every thread appends to whichever list is current. The cached list ends up holding up to four times the routes (195 to 240 entries for 60 routes), and it stays that way until routes change again.
  - `/openapi.json` then emits hundreds of "Duplicate Operation ID" warnings: 10/10 trials, including at the default switch interval with 150 realistic body-model routes.
  - A thread can also get back a list another thread is still building. One thread saw 45 of 60 distinct routes, so that request could 404.
- **Base result:** 0/10 trials. The base has no cache because routes are copied at include time.
- **Contract broken:** routing and OpenAPI must reflect each registered route exactly once.
- **Probes:** `p2_thread_race.py` (setswitchinterval 1e-6), `p2c_openapi_after_race.py` (end to end), `p2e_race_default_interval_bigger.py` (default interval). `p2_thread_race.py` imports `_IncludedRouter`, which does not exist at base, so the base comparison comes from `p2c` and `p2e`.

**2. A schema assigned to `app.openapi_schema` before the first `app.openapi()` call is thrown away (executed)**
- **Location:** `fastapi/applications.py`, `FastAPI.openapi()`. The new condition is `not self.openapi_schema or self._openapi_routes_version != routes_version`, and `_openapi_routes_version` starts as `None`.
- **Trigger:** setting `app.openapi_schema = {...}` (for example, loading a schema from a file) without also replacing `app.openapi`.
- **Head result:** `app.openapi()` and `GET /openapi.json` both return the generated schema (title "FastAPI"), overwriting the assigned one.
- **Base result:** the assigned schema is served (title "CUSTOM").
- **Variant (inferred):** if a user changes the dict returned by `app.openapi()` in place and a route is added later, the version changes and the changes are lost. At base they were kept. To show it: call `app.openapi()`, set `["info"]["x-logo"]`, add an `@app.get` route, call `app.openapi()` again and check whether `x-logo` survives.
- **Contract broken:** `openapi_schema` is the documented cache that users may assign.
- **Probe:** `p1_openapi_schema_preset.py`.

**3. Misconfigured include options now fail on every request instead of at `include_router` (executed)**
- **Location:** `fastapi/routing.py`. `include_router` now only stores an `_IncludedRouter`. The `_populate_api_route_state` assertions run lazily inside `effective_candidates()` → `_EffectiveRouteContext.from_api_route` on the first match or OpenAPI call. A failed build leaves the version unset, so every request retries it.
- **Trigger:** for example `app.include_router(r, responses={204: {"model": M}})`, or any include-level value that `_populate_api_route_state` rejects.
- **Head result:**
  - `include_router` succeeds, then `/x` and `/openapi.json` return 500 on every request.
  - Unrelated app routes declared after the include (`/health`) and unmatched paths (`/nope`) also return 500, with `AssertionError: Status code 204 must not have a response body`.
- **Base result:** `include_router` raises that assertion at startup.
- **Contract broken:** configuration errors should fail fast at startup and should not take down unrelated routes.
- **Probes:** `p3_lazy_error.py`, `p3b_lazy_error_blast_radius.py`.

## Dropped leads
- **`router.mount()` after include is ignored once the cache is warm** (`mount` and `host` don't bump `_routes_version`). Head gives 200 before the first request and 404 after. Base gives 404 in both cases, so this is not a regression (`p4b_mount_timing.py`).
- **Webhooks or direct `routes` mutation leave the OpenAPI cache stale.** Base caches the schema forever, so its result is the same or worse.
- **Race on the OpenAPI cache version.** `routes_version` is read before the schema is generated, so a schema built during a concurrent change is regenerated on the next call.
- **`_effective_route_context_var` ContextVar.** It is set and reset synchronously around `get_route_handler()`, and the value is per thread and per context, so it cannot leak.
- **Shared `scope["fastapi"]` dict.** `_IncludedRouter.matches` and `_match` restore their keys, and handle-time keys are checked by identity (`original_router is self`, `original_route is self`). Shallow scope copies such as the redirect-slashes check go through the same restore.
- **Version-sum collisions in `_get_routes_version`.** Every counter only increases and the seen-set handles cycles, so the sum is monotonic.
- **`_IncludedRouter` is an unhashable dataclass.** Starlette `Route` is unhashable at base too, so `set(app.routes)` already raised a `TypeError` (`p5_routes_hashable.py`).
- **Re-entrant cache build within one event loop.** The build has no `await`, so tasks cannot interleave inside it.
- **`get_route_handler()` now runs on every request for included routes.** This is a per-request cost and creates no shared state.
- **`p2b_thread_race_url_for.py`.** `url_path_for` never failed in 0/40 trials, because the duplicated list still contains the route. Candidate 1's partial-list case is the path to a miss.