I found four candidates I could not contradict; three were run at both base and head. The script that lists failure points flagged one added line, `copy.copy(route)` at `fastapi/routing.py:1495`. I dropped it because the base never included `Mount` routes (reason below). The checkout is unchanged and the base worktree has been removed.

All probes are in `<scratch>/out-arm/find-bugs-fastapi-0/.scratch/router-tree/search-1/finder-faults/probes/`. Each `pN_*.py` has a matching `.out` file, and the commands are in `COMMANDS.txt`.

## Candidates

**1. `include_router` errors now show up at request time and break unrelated routes (executed)**
- **Location:** `fastapi/routing.py`, `include_router` (now only appends `_IncludedRouter`) and `_IncludedRouter.effective_candidates`/`_build_effective_context`, which call `_populate_api_route_state` lazily from `matches()` and `url_path_for()`.
- **Trigger:** an include configuration that fails when the effective route is built. Three tried:
  - `include_router(r, prefix="/api", responses={204: {"model": M}})`
  - `dependencies=[Depends("not-callable")]`
  - a `generate_unique_id_function` that raises
- **Base:** `include_router` raises `AssertionError` or `RuntimeError` at import time. The rest of the app keeps working.
- **Head:** `include_router` succeeds.
  - Every later request returns 500, because the error is raised while matching: routes registered after the include, the included routes, unknown paths that should be 404, and `/openapi.json`.
  - `app.url_path_for("after")` raises the same `AssertionError` instead of returning `/after`.
  - Only routes listed before the include still work. This repeats on every request because nothing is cached when the build fails.
- **Contract broken:** a misconfiguration failed fast at startup. Now it is an app-wide runtime outage that a health check on an earlier route would not catch.
- **Probe:** `p1_deferred_include_error.py` / `.out`

**2. Exception handlers and middleware see the route without its prefix in `scope["route"]` (executed)**
- **Location:** `_IncludedRouter._handle_selected` sets `scope["route"] = original_route`, and `APIRoute.matches` sets `child_scope["route"] = self`.
- **Trigger:** an app exception handler or HTTP middleware reads `request.scope["route"].path` or `.path_format` for a route served through `include_router(prefix=...)`. Logging and metrics labelling commonly do this.
- **Base:** `/api/v1/boom/{item_id}`, and `/api/inner/ok` for a nested include.
- **Head:** `/boom/{item_id}` and `/ok`. The include prefix is gone, and two inclusions of the same router can no longer be told apart. `url_for` still resolves correctly.
- **Contract broken:** `scope["route"]` used to describe the full path that matched. Websocket routes still show the full path (`/api/ws`).
- **Probe:** `p3_exception_handler_route.py` / `.out` and `p2_exceptions_through_include.py` / `.out`

**3. `get_route_handler()` now runs on every request for included routes (executed)**
- **Location:** `APIRoute.handle`, which calls `request_response(self.get_route_handler())` on every request when an effective context is present.
- **Trigger:** a custom `APIRoute` subclass (the documented custom-route-class hook) whose `get_route_handler` does one-time setup. The probe registers a named metric and raises on a duplicate.
- **Base:** called once per route instance at construction (2 calls, for the original and the copy). All requests return 200.
- **Head:** called once per request on the same instance (4 calls after 3 requests). Every request returns 500 because the hook raises on the repeated call.
- **Contract broken:** the handler used to be built once at construction. Now the cost and any side effects repeat on every request.
- **Probe:** `p7_get_route_handler_per_request.py` / `.out`

**4. Two threads building the lazy route cache at once corrupt it permanently (executed at head only)**
- **Location:** `_IncludedRouter.effective_candidates`. It resets `self._effective_candidates = []`, appends through the attribute, and sets the version afterwards, with no lock.
- **Trigger:** a cache build in a worker thread overlaps one in the event loop. Example: a sync endpoint calls `request.url_for()` in the threadpool while the loop matches a request into an included router that has not been built yet, or one whose routes changed.
- **Base:** has no lazy cache. Routes are copied once in `include_router`.
- **Head, forced interleaving:** a short sleep wrapped around `_build_effective_context`. One caller got the routes out of declaration order (`r2, r0, r3, r1, r4`). The cache kept 8 entries with duplicates, and the version was marked current, so it stays that way.
- **Head, no instrumentation:** with `sys.setswitchinterval(1e-6)`, 198 of 200 trials left a duplicated cache.
- **Not observed:** I did not show a wrong route being chosen because of the reordering.
- **Contract broken:** route order decides precedence. Before this change the route table could not change after startup.
- **Probes:** `p5_lazy_cache_race.py` / `.out` (instrumented), `p6_lazy_cache_race_uninstrumented.py` / `.out`

## Dropped leads
- **`copy.copy(route)` for `Mount` (line 1495):** the base `include_router` skipped `Mount` and `Host` routes entirely, so the base handled no failure here to compare against.
- **Router-level dependency raising `HTTPException(403)`; a yield dependency seeing the endpoint's exception; 422 on bad path params:** base and head give the same results (p2).
- **Websocket dependency raising `WebSocketException(4403)`, 405 with the `Allow` header, and the 307 slash redirect through an included router:** same at base and head (p4).
- **Partial cache left behind when a build raises:** the version is only set after a successful build, so the next call rebuilds. The visible effect is candidate 1.
- **ContextVar left set when `get_route_handler` raises:** it is reset in a `finally` block. The `matches()` scope keys are also restored in `try/finally`.
- **Stale `scope["fastapi"]` keys after `_IncludedRouter.handle` and `_handle_selected`:** they are only read for a route reached directly, and only if a middleware re-dispatches the same scope. I found no supported path where that happens.
- **Lifespan and `on_startup`/`on_shutdown` merging:** the code is unchanged. Handlers added to a sub-router after it is included are lost at base too.

## Outside my focus (inferred, not probed)
- `app.openapi()` now regenerates the schema when `_openapi_routes_version` is `None`, so an `app.openapi_schema` the user set directly, without first calling `app.openapi()`, gets overwritten.
- Starlette's `router.mount()` and `router.host()` do not call `_mark_routes_changed()`, so a mount added to a sub-router after it is included stays unreachable through the cached tree.