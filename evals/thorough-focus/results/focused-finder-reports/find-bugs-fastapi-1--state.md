I found 6 candidates (5 executed, 1 a minor performance observation) and dropped 4 leads. This was one read covering the shared state the change adds: the `_IncludedRouter` candidate cache and its version counters, the new `app.openapi()` cache key, the `scope["fastapi"]` dict, the ContextVar, and the route handlers now built per request.

Each probe runs against both commits through `run.sh`, which sets `PYTHONPATH` to a disposable base (`016ab760`) or head (`1e70f7cd`) worktree and uses `/tmp/real-pr-cache/fastapi/venv/bin/python`. Each `.out` file holds the exact command and the base and head output. Probes are in `<scratch>/out-arm/find-bugs-fastapi-1/.scratch/router-tree/search-1/finder-state/probes/`. I removed my two worktrees, and the checkout is unchanged at `1e70f7c`.

## Candidates

**1. `app.openapi()` overwrites a schema the user assigned** (executed)
- **Location:** `fastapi/applications.py:1083-1084`. `_openapi_routes_version` starts as `None`, so the condition `self._openapi_routes_version != routes_version` is true on the first call.
- **Trigger:** `app.openapi_schema = {...}` (for example a schema loaded from a file), then `/openapi.json` or `app.openapi()`.
- **Base:** returns the assigned schema (title `PRESET`).
- **Head:** builds a new schema and discards the assigned one (title `FastAPI`).
- **Related:** if the user edits the dict that `app.openapi()` returned (for example adds `x-logo`), the next route addition anywhere in the tree throws the edit away.
- **Contract broken:** `openapi_schema` is a public attribute that `openapi()` treated as authoritative once it was set.
- **Probe:** `p1_preset_openapi_schema.py` / `.out`

**2. Include-time validation now runs on the first request, and a bad include breaks routes added after it** (executed)
- **Location:** `routing.py` `_IncludedRouter.effective_candidates()` builds its cache lazily and calls `_EffectiveRouteContext.from_api_route` → `_populate_api_route_state`. `include_router` no longer validates the combined route.
- **Trigger:** `app.include_router(r, responses={204: {"model": M}})` where `r` has a 204 route.
- **Base:** `include_router` raises `AssertionError: Status code 204 must not have a response body` at startup.
- **Head:** the include is accepted. Every request to a route registered after that include returns 500, and so does `/openapi.json`. Because the cache version is never recorded when the build raises, the failure repeats on every request.
- **Contract broken:** route configuration errors should fail at startup instead of turning unrelated endpoints into 500s.
- **Probe:** `p2_lazy_include_validation.py` / `.out`

**3. Thread race on the `_IncludedRouter._effective_candidates` cache** (executed, interleaving forced)
- **Location:** `effective_candidates()` sets `self._effective_candidates = []`, appends through the attribute, sets the version last, and returns the attribute rather than a local list.
- **Trigger:** two threads build the cache at the same time before it exists, for example `request.url_for(...)` or `app.openapi()` called from sync endpoints in the threadpool.
- **Base:** `url_path_for` works in both threads.
- **Head:**
  - Thread A gets `NoMatchFound` for `r0` because it returns thread B's partly built list.
  - While B is paused, the version is already recorded, so `GET /p/r0` from any reader returns 404.
  - Once both finish, the cache holds `['r1','r2','r0','r1','r2']` and stays that way until the next route change; openapi then warns `Duplicate Operation ID`.
- **Contract broken:** routing and URL building must not depend on when threads arrive.
- **Probe:** `p3_thread_race_effective_candidates.py` / `.out`. The wrapper around `from_api_route` only delays threads with events; it does not change any state.

**4. Route handlers are rebuilt on every request for included routes, so state kept in the handler closure resets** (executed)
- **Location:** `APIRoute.handle` (new) calls `request_response(self.get_route_handler())` on every request when an effective context is present.
- **Trigger:** a custom `route_class` that overrides `get_route_handler`.
- **Base:** `get_route_handler` runs 0 times over 100 requests, and closure state accumulates (`x-count` reads 1, 2, 3).
- **Head:** `get_route_handler` runs 100 times over 100 requests, and closure state resets every time (`x-count` reads 1, 1, 1).
- **Contract broken:** `get_route_handler` is a documented extension point whose result was built once per route.
- **Probe:** `p6_handler_rebuilt_per_request.py` / `.out`

**5. `scope["route"]` and `self` in custom handlers show the original route, not the included one** (executed)
- **Location:** `APIRoute.matches` sets `child_scope["route"] = self`, and `_IncludedRouter._handle_selected` sets `scope["route"] = original_route`.
- **Trigger:** a route reached through `include_router(prefix="/p", tags=["T"], dependencies=[...])`.
- **Base:** `scope["route"].path` is `/p/x`, `self.tags` is `['T']`, and there is 1 dependency.
- **Head:** `scope["route"].path` is `/x`, `self.tags` is `[]`, and there are 0 dependencies.
- **Contract broken:** middleware and metrics that label by `scope["route"].path` see the wrong value, and identical paths in different routers collide.
- **Probe:** `p7_custom_handler_sees_route_state.py` / `.out`

**6. Sub-router changes made without bumping the version are invisible after the first request** (executed, not a regression from base)
- **Location:** `_get_routes_version` and `_mark_routes_changed` only track `add_api_route`, `add_route`, websocket routes and includes. Starlette's `Router.mount` and `Router.host`, and direct `routes.append`, do not bump the version.
- **Trigger:** a sub-router change made after the included router's cache was built.
- **Base:** 404 in every case.
- **Head:** 200 when the change happens before the first request; 404 for `mount` and `routes.append` after it. `add_api_route` works in both cases.
- **Contract broken:** the release note says "adding routes after a router is included now works", but whether a change is visible now depends on whether a request has been served.
- **Probe:** `p4_untracked_mutations.py` / `.out`

**Minor observation:** 2000 direct ASGI requests to a route behind three nested includes, with 50 routes per router, took 0.59s on base and 1.20s on head. This comes from the per-request version walk at each nesting level plus the per-request handler rebuild. Whether it matters depends on app size and traffic. Probe: `p8_per_request_overhead.py` / `.out`.

## Dropped leads
- **Routes became unhashable dataclasses:** Starlette `Route` is already unhashable on base, and `.index()` equality behaves the same (`p5_route_identity.out`).
- **Async race on the candidate cache:** `effective_candidates()` and `_match` contain no `await`, so tasks on a single event loop cannot interleave there.
- **Leftover `scope["fastapi"]` keys misrouting a nested mount or sub-app:** every consumer checks `original_route is self` or `original_router is self`, and `_IncludedRouter.matches` restores its key in a `finally`.
- **Version-sum collisions in `_get_routes_version`:** the counters only increase, and the diamond `seen` set still counts each router once. A lost `+=` would need routes registered from two threads at once, which I judged too contrived to keep.