I found three candidates in this one read: two in the failure-mode scope, plus one outside it. The probes ran at both base and head (worktrees at 016ab760 and 1e70f7cd), and the worktrees have since been removed. The checkout is unchanged (`git status` is clean). Probes, their outputs and `COMMANDS.txt` are in `<scratch>/out-arm/find-bugs-fastapi-1/.scratch/router-tree/search-1/finder-faults/probes/`.

`failure_points.py` listed one added failure point, `copy.copy(route)` for a Mount at `fastapi/routing.py:1495`. It did not lead to a candidate (see the dropped leads). The search then turned to user code that raises during router inclusion and request handling.

## Candidates

**1. Invalid include arguments and failing user callbacks no longer raise at `include_router`. They break every request after that point in the route list, and `/openapi.json`.**
- **Location:** `fastapi/routing.py:2459`. `include_router` now only appends `_IncludedRouter`. The include context is computed lazily in `_IncludedRouter.effective_candidates` (`routing.py:1431`) through `_build_effective_context` and `_populate_api_route_state`. That runs inside `matches()` on every request, and inside `url_path_for` and `openapi`. When it raises, the version is never recorded, so the rebuild and the error repeat on every request.
- **Trigger, any of:**
  - `include_router(r, dependencies=[Depends()])`
  - `include_router(r, responses={204: {"model": M}})`
  - a `generate_unique_id_function` that raises
  - a prefix whose path parameter repeats a route's, such as `prefix="/t/{id}"` with route `/{id}`
  - a route with that clash added to the sub-router after it was included
- **Base result:** `include_router` raises `AssertionError`, `RuntimeError` or `ValueError` at configuration time, so the app fails at import. In the variant where the route is added after inclusion, the route is silently not exposed: 404 for it, 200 for every other route.
- **Head result:** `include_router` accepts the arguments and the app starts. Then:
  - Routes registered before the include return 200.
  - The included routes, every route registered after the include, unknown paths (404s) and `/openapi.json` all return 500.
  - `app.url_path_for` and `app.openapi()` raise the original error.
- **Contract broken:**
  - Configuration errors used to fail fast at `include_router`.
  - A misconfigured router should not take down unrelated routes.
  - The release notes say adding routes after inclusion "now works", but one bad late route turns the whole app into a 500 at request time.
- **Probes (executed):** `p1_deferred_include_errors.py` with output `p1.out`, and `p3_prefix_param_collision.py` with output `p3.out`.

**2. A custom `APIRoute.get_route_handler()` now runs on every request for included routes, so per-request failures replace one-time setup.**
- **Location:** `fastapi/routing.py:1180`. `APIRoute.handle` calls `request_response(self.get_route_handler())` on every request when an effective context exists.
- **Trigger:** a `route_class` subclass whose `get_route_handler` does setup that cannot be repeated (for example, registering a metric whose second registration raises), or that raises.
- **Base result:** it runs twice in total at setup (original plus the copy made at include) and never at request time. The probe returned 200 on three requests.
- **Head result:** it runs once at setup, then again on every request. With a "duplicate registration raises" handler, every request returned 500.
- **Contract broken:**
  - `get_route_handler` is the documented one-time customisation hook (custom request and route class docs).
  - Errors and side effects move from startup into each request.
  - There is also a per-request cost: `get_request_handler` is rebuilt on every request.
- **Probe (executed):** `p2_route_class_handler_per_request.py` with output `p2.out`.

**3. (Outside the failure-mode focus, passed on as a lead.) `FastAPI.openapi()` now throws away a schema the user assigned or edited.**
- **Location:** `fastapi/applications.py:1083-1084`. The schema is regenerated whenever `_openapi_routes_version` differs, and that value starts as `None`.
- **Trigger:**
  - Assigning `app.openapi_schema = {...}` before the first `app.openapi()` call.
  - Editing the dict returned by `app.openapi()` in place, then adding a route.
- **Base result:** both the preset schema and the in-place edit are kept.
- **Head result:** both are lost on the next `app.openapi()` call.
- **Probe (executed):** `p4_openapi_schema_preset.py` with output `p4.out`.

## Dropped leads
- **`copy.copy(route)` for a Mount (`routing.py:1495`):** Starlette's `Mount` defines neither `__copy__` nor `__reduce__`, so the shallow copy cannot fail on supported input. The base dropped Mount routes in `include_router` altogether, so it handled no such case either.
- **User code raising during request handling in included routes:** `p5_request_time_raises.py` (`p5.out`) gave identical results at base and head for each of these:
  - an include-level dependency raising an exception that an app exception handler catches (418)
  - teardown of a `yield` dependency (enter then exit)
  - app `dependency_overrides`
  - 405 for a wrong method
  
  The contextvar is also back to `None` after the requests.
- **Scope keys left set after an error:** the keys under `scope["fastapi"]` are restored in a `finally` block in `_match` and `_IncludedRouter.matches`. The ones left set by `handle` and `_handle_selected` are reset on the next match, so a re-dispatch with the same scope (redirect slashes, a rewrite middleware) re-matches correctly.
- **Partial `_effective_candidates` list after an exception:** the version is not recorded, so the next call rebuilds the list. No partial list is ever returned on a single thread. A race between a threadpool `url_path_for` and event-loop matching during a rebuild is possible in principle, but needs routes to change at runtime and was not probed.
- **Lifespan and startup merging in `include_router`:** the code is unchanged from the base.
- **Host route with an empty prefix:** the base raised `AttributeError` from `getattr(r, "path")` and the head passes a default, so this is an improvement, not a regression.