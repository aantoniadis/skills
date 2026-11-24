I found 8 candidates I could not contradict, all executed at both commits. This was one read, comparing base 016ab760 with head 1e70f7cd. Probe files and the runner are in `<scratch>/out-arm/find-bugs-fastapi-1/.scratch/router-tree/search-1/finder-general/probes/`, and the outputs are saved in `results.log` there.

**Command for every probe:** `./run.sh <probe>.py`. It runs the probe with `-I` and the venv Python, once against a base worktree and once against a head worktree. The output confirms each run imported fastapi from its own worktree. I have removed my worktrees, the checkout has no changes, and I did not touch the lead's worktrees.

## Candidates

1. **`request.scope["route"]` lost the include prefix** (`fastapi/routing.py:1162`, `:1593`)
   - **Trigger:** `app.include_router(APIRouter(prefix="/users"), prefix="/api")`, then read `scope["route"]` in an endpoint or middleware.
   - **Base:** `path` is `/api/users/{user_id}`.
   - **Head:** `path` and `path_format` are `/users/{user_id}`. The route in scope is the original, unprefixed `APIRoute`, and it lacks include-level tags.
   - **Contract broken:** the route in scope should carry the path template that was matched. Metrics and tracing middleware that label requests with `scope["route"].path` now get the wrong path. The release notes list only `router.routes` as breaking, not this.
   - **Probe:** `p1_scope_route_path.py`

2. **A schema assigned to `app.openapi_schema` is thrown away** (`fastapi/applications.py:1083-1084`)
   - **Trigger:** set `app.openapi_schema = {...}` without overriding `app.openapi`, then GET `/openapi.json`.
   - **Base:** serves the assigned schema (title `CUSTOM`).
   - **Head:** `_openapi_routes_version` starts as `None`, so the check never matches and the schema is regenerated (title `FastAPI`).
   - **Contract broken:** `openapi_schema` worked as a user-settable cache.
   - **Same probe, second part:** changes made inside the dict returned by `app.openapi()` are lost when a route is added later. That may be intended under the new live-routes behaviour; your call.
   - **Probe:** `p2_openapi_schema_assign.py`

3. **`generate_unique_id_function` receives an `_EffectiveRouteContext`, not an `APIRoute`** (`fastapi/routing.py:985`, called from `from_api_route` at `:1340`)
   - **Trigger:** `FastAPI(generate_unique_id_function=f)` where `f` uses `isinstance(route, APIRoute)` or any `APIRoute`/`Route` member the context lacks. Applies to any included router.
   - **Base:** `f` gets an `APIRoute`.
   - **Head:** `f` gets an `_EffectiveRouteContext`, and the assertion fails inside `app.openapi()`.
   - **Contract broken:** the parameter is typed `Callable[[APIRoute], str]`, and the docs this change rewrites say "The function receives each `APIRoute`".
   - **Probe:** `p3_unique_id_arg.py`

4. **Callbacks from a callback router that includes another router disappear from OpenAPI** (`fastapi/openapi/utils.py:325-326`)
   - **Trigger:** `cb.include_router(inner)`, then `@app.post(..., callbacks=cb.routes)`. Router-level and include-level `callbacks=` take the same path.
   - **Base:** the `callbacks` object holds `on_event`.
   - **Head:** `callbacks: {}`. The loop at that spot keeps only `isinstance(callback, APIRoute)` and never expands `_IncludedRouter`. The `Event` model is still collected (via `get_fields_from_routes`), so nothing errors and the gap is silent.
   - **Contract broken:** callback documentation in OpenAPI.
   - **Probe:** `p4_callback_nested.py`

5. **A false "Prefix and path cannot be both empty" error for nested routers** (`fastapi/routing.py:2438-2444` with `_iter_included_route_candidates` at `:1614`)
   - **Trigger:** `inner` has `@inner.get("")`, then `outer.include_router(inner, prefix="/items")`, then `app.include_router(outer)` with no prefix.
   - **Base:** includes fine, and GET `/items` returns `inner-root`.
   - **Head:** raises `FastAPIError`. The check now sees the original route's path `""` rather than the prefixed `/items`.
   - **Contract broken:** a valid configuration now fails at startup.
   - **Probe:** `p7_empty_path_nested.py`

6. **Include-time configuration errors are deferred and break unrelated requests** (`fastapi/routing.py:1431-1450`, `:1021`)
   - **Trigger:** `app.include_router(r, responses={204: {"model": Item}})`.
   - **Base:** `AssertionError` at `include_router` ("Status code 204 must not have a response body").
   - **Head:** no error at startup. Then GET `/a` returns 500, and so does GET `/nope` (an unknown path that should be 404). Routes listed before the included router still return 200.
   - **Mechanism:** route contexts are built lazily on the first match, and the assertion fires during matching.
   - **Contract broken:** the app no longer fails fast at startup, and every request routed past the included router returns 500.
   - **Probe:** `p9_deferred_validation.py`

7. **The request handler is rebuilt on every request for included routes** (`fastapi/routing.py:1178-1183`)
   - **Trigger:** any request to a route in an included router.
   - **Base:** `get_route_handler` is built once at startup (0 calls during 5 requests). A minimal GET takes about 28–35 µs.
   - **Head:** 5 calls for 5 requests, about 50 µs per request. Each request also matches twice (`matches`, then `_handle_selected` → `_match`), and `_get_routes_version` walks the tree on each match.
   - **Contract broken:** the rewritten docs promise no added overhead per request. Custom `APIRoute.get_route_handler` overrides now run once per request, so any side effects there repeat per request.
   - **Probe:** `p5_handler_per_request.py`. These are timing figures from one machine.

8. **A sub-router included late is served, but its lifespan never runs** (`fastapi/routing.py:2466-2469`)
   - **Trigger:** `app.include_router(router)`, then `router.include_router(sub)` where `sub` has a `lifespan`. The rewritten docs now say this order works.
   - **Base:** 404 (the route was never added), and the lifespan did not run.
   - **Head:** 200 with `request.state.db` set to `None`, and the lifespan did not run. The app already captured the old `router.lifespan_context` when the router was included.
   - **Contract broken:** a failure that used to be loud is now silent, on a path the docs newly advertise.
   - **Probe:** `p10_late_include_lifespan.py`

**Inferred, not probed:** a thread race in `_IncludedRouter.effective_candidates` (`:1435`). The cached list is set to `[]` and then refilled in place. If `request.url_for` is called from a sync endpoint (threadpool) while the event loop is matching, and routes were added at runtime, one side can see an empty list and get 404 or `NoMatchFound`. To settle it: add a route at runtime while hammering `url_for` from a sync endpoint, and count the failures.

## Dropped leads
- **Routing behaviour through included routers:** dependency overrides, 405 with `Allow`, slash redirect, 404, 422, websocket with dependencies, `url_for` and `app.url_path_for` all match between base and head (`p6_sanity.py`).
- **`app.routes` entries unhashable:** Starlette's `Route` is already unhashable at base (`p8_hashable.py`).
- **Stream item type lost for JSONL endpoints in included routers:** the base passes `response_model=route.response_model` when it re-creates the route the same way, so this predates the change.
- **Per-router metadata inheritance:** tags, dependencies, responses, `default_response_class`, `generate_unique_id_function`, `strict_content_type`, `deprecated`, `include_in_schema`, `dependency_overrides_provider` and callbacks resolve in the same order as the base, traced by hand across two levels.
- **OpenAPI cache-version collisions:** the summed version only grows, and the `seen` set counts a shared router's subtree on its first visit, so the value cannot repeat.
- **Code that iterates or mutates `app.routes` / `router.routes`** (the old operationId recipe, starlette-exporter style matching): the release notes declare this a breaking change.
- **Leftover `scope["fastapi"]` keys after a request is handled:** every use is guarded by an `original_route is self` or `original_router is self` check, and I found no path where a leftover key misleads.
- **`Mount` and `Host` inside included routers:** the base dropped them silently, so serving them is new behaviour, not a regression.