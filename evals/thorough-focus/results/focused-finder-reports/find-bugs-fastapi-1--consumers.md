I found 13 candidates I could not contradict; 12 are executed and 1 is inferred. This was one read focused on what code outside the change sees, comparing base 016ab760 with head 1e70f7cd.

Probes are in `<scratch>/out-arm/find-bugs-fastapi-1/.scratch/router-tree/search-1/finder-consumers/probes/`. To run one, go to that folder and run `./run.sh pNN_*.py`, which runs it at base and then at head. Before that, recreate the two worktrees as `COMMANDS.txt` there describes, because I removed them when done. The outputs are in `results-1.txt` to `results-5.txt` in the same folder. The checkout is unchanged.

## Candidates

1. **An `APIRoute` subclass that overrides `matches()` serves an included route at the wrong URL** (executed, p17)
   - **Location:** `_IncludedRouter._match` calls `candidate.original_route.matches(scope)`, in `fastapi/routing.py`, roughly head lines 1530–1545.
   - **Trigger:** a subclass with its own match logic, for example a header guard that calls `starlette.routing.Route.matches(self, scope)`, on a router included with `prefix="/p"`.
   - **Base:** `GET /p/x` returns 200 and `GET /x` returns 404.
   - **Head:** `GET /p/x` returns 404 and `GET /x` returns 200.
   - **Contract:** the prefix given to `include_router` decides the URL. The release notes also advertise subclassing as the supported way to customize matching.

2. **An `APIRoute` subclass whose `handle()` calls `self.app` skips include-level dependencies** (executed, p16)
   - **Location:** `APIRoute.handle` builds the handler that uses the include settings only when the subclass calls `super().handle`. `self.app` still holds the original route's handler, which lacks those dependencies.
   - **Trigger:** `include_router(router, dependencies=[Depends(auth)])`, where the subclass's `handle` ends in `await self.app(scope, receive, send)`, the same thing Starlette's `Route.handle` does.
   - **Base:** 401.
   - **Head:** 200 with the protected body.
   - **Contract:** dependencies given to `include_router` run for every included operation. Here an auth dependency is bypassed.

3. **Wrappers set on `self.app` in a subclass `__init__` are skipped for included routes** (executed, p05)
   - **Trigger:** a subclass that wraps `self.app` after `super().__init__`.
   - **Base:** the wrapper runs (`['/p/x']`).
   - **Head:** the wrapper never runs (`[]`).
   - **Cause:** the head never calls the subclass constructor for included routes, and `APIRoute.handle` builds a new handler with `request_response(self.get_route_handler())` instead of using `self.app`.

4. **`request.scope["route"]` is the original route, without the prefix, tags or dependencies from the include** (executed, p01 and p10)
   - **Location:** `_IncludedRouter._handle_selected` sets `scope["route"] = original_route` (around head line 1593), and `APIRoute.matches` sets `child_scope["route"] = self`.
   - **Base:** `path` is `/api/items/{item_id}`, tags are `['x', 'r']`, and there is 1 dependency.
   - **Head:** `path` is `/items/{item_id}`, tags are `['r']`, and there are 0 dependencies.
   - **Same router included twice** (`/v1` and `/v2`): at the head both requests get the same object with `path` `/x`. At the base they got distinct routes, `/v1/x` and `/v2/x`.
   - **Consumers affected:** middleware and tracing tools that read `scope["route"].path`. They get wrong route names that collide.

5. **Inside an `APIRoute` subclass, `self.path` and `self.tags` lack the include values** (executed, p12)
   - **Trigger:** a subclass whose `get_route_handler` logs `self.path` and `self.tags`.
   - **Base:** `('/api/x', ['t'])`.
   - **Head:** `('/x', [])`.

6. **Iterating `app.routes` and reading `.path` on a match raises `AttributeError`** (executed, p02)
   - **Location:** `_IncludedRouter` has no `path` attribute.
   - **Trigger:** the matching code that instrumentation libraries use: `for r in app.routes: m, _ = r.matches(scope); if FULL: r.path`.
   - **Base:** matches an `APIRoute` with path `/api/items/{item_id}`.
   - **Head:** `AttributeError: '_IncludedRouter' object has no attribute 'path'`.
   - **Note:** the release notes call this a breaking change. I list it because it raises on every request through that kind of tool, rather than silently returning different data.

7. **Callbacks disappear from OpenAPI when the callback router includes another router** (executed, p03)
   - **Location:** `get_openapi_path` in `fastapi/openapi/utils.py`, around line 325, keeps the `if isinstance(callback, routing.APIRoute)` loop and never walks into `_IncludedRouter`. `get_fields_from_routes` was updated; this loop was not.
   - **Trigger:** `@app.post(..., callbacks=cb_router.routes)` where `cb_router.include_router(cb_inner)`.
   - **Base:** a callback named `cb` with its path.
   - **Head:** `callbacks: {}`.
   - **Contract:** `openapi-callbacks.md`, which this change edits, says to pass `.routes`.

8. **An `app.openapi_schema` set by the user is overwritten** (executed, p04)
   - **Location:** `FastAPI.openapi` in `fastapi/applications.py`. `_openapi_routes_version` starts as `None`, so the first call always regenerates.
   - **Trigger:** `app.openapi_schema = {...custom...}` without overriding `app.openapi`.
   - **Base:** `app.openapi()` and `/openapi.json` both return the custom title.
   - **Head:** both return the generated schema (title `FastAPI`).
   - **Second case:** a schema mutated after `app.openapi()` (adding `x-logo`) loses the change once a route is added. Base keeps the mutation (and serves the stale paths); head regenerates and drops it.

9. **`generate_unique_id_function` now receives `_EffectiveRouteContext`, not `APIRoute`** (executed, p06)
   - **Base:** the hook receives `APIRoute`, and `isinstance(route, APIRoute)` is True.
   - **Head:** the hook receives `_EffectiveRouteContext`, `isinstance` is False, and a hook that asserts the type raises `AssertionError`.
   - **Contract:** the public type is `Callable[[APIRoute], str]`, and the rewritten docs say "The function receives each `APIRoute`".

10. **Nested include without a prefix raises a false "Prefix and path cannot be both empty"** (executed, p08)
    - **Location:** the empty-prefix check in `include_router` reads `_iter_included_route_candidates`. For API routes, that yields the original route, whose path does not yet carry the inner prefix.
    - **Trigger:** `S` has `@S.get("")`, `R.include_router(S, prefix="/s")`, then `app.include_router(R)` with no prefix.
    - **Base:** includes fine, and `GET /s` returns `{'s': 1}`.
    - **Head:** `FastAPIError` when including.

11. **The previously documented `operationId` recipe no longer affects included routes** (executed, p15)
    - **Trigger:** the old pattern from `docs_src` tutorial002: loop over `app.routes` and set `route.operation_id = route.name`.
    - **Base:** `read_items`.
    - **Head:** `read_items_api_items__get`.
    - **Docs:** the English page was rewritten. The 11 translated `path-operation-advanced-configuration.md` pages (de, es, fr, ja, ko, pt, ru, tr, uk, zh, zh-hant) still describe the loop and highlight `hl[2, 12:21, 24]`, but the shared example file is now 14 lines with different content. The `bigger-applications` page is likewise updated only in English; I saw this from the diff and did not open the translations.

12. **A subclass `get_route_handler` now runs on every request for included routes** (executed, p07)
    - **Base:** 0 calls across 5 requests.
    - **Head:** 5 calls.
    - **Effect:** side effects in that hook repeat per request, and the full request handler is rebuilt per request. That conflicts with the docs claim of no added per-request overhead. In my end-to-end timing (p13, 3 levels deep, 40 routes per router) the head was about 7% slower: 2.89 vs 3.10 ms per request, mostly test-client overhead.

13. **(inferred) Routes added with Starlette's `router.mount()` or `router.host()` after a request has been served do not appear** — not probed
    - **Cause:** those methods do not bump `_routes_version`, so the cached `_effective_candidates` stay stale.
    - **Base:** mounts in included routers were silently dropped, so this is not a regression. It does contradict the new "live inclusion" claim in the docs.
    - **Probe to run:** include router `R`, send one request, call `R.mount("/m", sub_app)`, then `GET /prefix/m/...`. Predicted: 404 at the head.

## Dropped leads
- **Dependency overrides, `url_for` (API route and plain route), and 405 with the Allow header through nested includes:** base and head are identical (p09).
- **Hash, eq, membership, copy, and `deepcopy` on items of `app.routes`:** same at base and head. Both are unhashable, and `deepcopy` hits a RecursionError on both (p11).
- **Streaming item schema lost for included routes:** happens at the base too (p14), so it predates the change.
- **Merge order of tags, dependencies, responses, deprecated, `include_in_schema`, response class and unique-id function:** reading `for_include` and `combine` against the base `include_router` and `add_api_route` shows the same order.
- **`get_openapi(routes=...)` changed from `list(routes or [])` to `list(routes)`:** the parameter is a required `Sequence`, and passing `None` was already outside the contract.
- **Mount, Host and `add_route` in included routers:** the base dropped Mount and Host silently; the head serves them. This is new behavior, not a regression.
- **Per-request cost from double matching at each nesting level:** about 7% in p13, which is not material by itself. It is noted under candidate 12.