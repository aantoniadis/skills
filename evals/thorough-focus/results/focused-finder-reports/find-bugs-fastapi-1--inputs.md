This was one read of the change from 016ab760 (base) to 1e70f7cd (head). I found 9 candidates that I could not contradict, and all of them were run on both base and head. Probes, `run.sh` and the result files are in `<scratch>/out-arm/find-bugs-fastapi-1/.scratch/router-tree/search-1/finder-inputs/`. `COMMANDS.txt` there gives the command: `./run.sh $PWD/<probe>.py` runs a probe on base, then on head. I removed both worktrees afterwards, and `git status` on the checkout is clean.

## Candidates (all executed)

1. **`scope["route"]` loses the include-level prefix and settings.** `APIRoute.matches` and `_IncludedRouter._handle_selected` now put the original route in `scope["route"]`, where they used to put a cloned copy.
   - **Trigger:** a route in a router included with `prefix="/api", tags=["t"]`, where code reads `request.scope["route"]`.
   - **Base:** `path='/api/items/{item_id}'`, `tags=['t']`.
   - **Head:** `path='/items/{item_id}'`, `tags=[]`.
   - **Contract broken:** middleware, logging and metrics that label requests by the route template (the common instrumentation pattern) now get the wrong path.
   - **Probe:** `p01_scope_route_path.py`

2. **Wrong empty-path error for nested includes.** `include_router` checks `_iter_included_route_candidates`, which returns the original `APIRoute` without the prefix of the inner include.
   - **Trigger:** router `c` includes `g` with `prefix="/g"`, and `g` has `@g.get("")`. Then `app.include_router(c)` is called with no prefix.
   - **Base:** `GET /g` returns 200.
   - **Head:** raises `FastAPIError: Prefix and path cannot be both empty`.
   - **Contract broken:** valid setups are rejected.
   - **Probe:** `p02_empty_prefix_nested.py`

3. **A schema set on `app.openapi_schema` is overwritten.** In `fastapi/applications.py`, `openapi()` regenerates when `_openapi_routes_version` (which starts as `None`) differs from the router's version.
   - **Trigger:** setting `app.openapi_schema = {...}` without calling `app.openapi()` first.
   - **Base:** serves the custom schema (`title: 'custom'`).
   - **Head:** regenerates it (`title: 'FastAPI'`).
   - **Contract broken:** the previous rule was that a non-empty cached schema is served as is.
   - **Probe:** `p03_preset_openapi_schema.py`

4. **Include-time validation now happens at request time and breaks unrelated routes.** `_EffectiveRouteContext.from_api_route` is built lazily the first time a route is matched.
   - **Trigger:** `app.include_router(r, responses={204: {"model": M}})`, followed by any request.
   - **Base:** `AssertionError` when `include_router` is called, at startup.
   - **Head:** the include succeeds. After it, every request that has to try this include returns 500, including the unrelated route `/later` registered after it; `/ok`, registered before it, still returns 200.
   - **Contract broken:** configuration errors used to fail at startup.
   - **Probe:** `p04_include_validation_deferred.py`

5. **Callbacks from a router that includes another router disappear from OpenAPI.** In `fastapi/openapi/utils.py`, `get_openapi_path` loops over `route.callbacks` with `isinstance(callback, routing.APIRoute)`, so `_IncludedRouter` entries are skipped.
   - **Trigger:** `callbacks=cbr.routes`, where `cbr.include_router(inner)`.
   - **Base:** the `cb` callback is in the schema.
   - **Head:** `callbacks: {}`.
   - **Contract broken:** OpenAPI callbacks documentation is lost silently.
   - **Probe:** `p05_callbacks_nested.py`

6. **Plain Starlette routes in a nested include move to a new URL.** `_IncludedRouter._build_effective_context` builds the path with `path_for`, which now includes the parent router's prefix.
   - **Trigger:** a prefixed `APIRouter` includes a router that has an `add_route("/plain", ...)` route.
   - **Base:** `/top/c/plain` returns 200 and `/top/parent/c/plain` returns 404.
   - **Head:** the reverse.
   - **Contract:** this is the *you decide* item. Head is more consistent with how `APIRoute` paths work, but existing URLs break, and plain routes added directly to the prefixed router still get no prefix. The same code path applies to plain `WebSocketRoute`, which I did not probe.
   - **Probe:** `p10_plain_route_parent_prefix.py`

7. **`get_openapi(routes=None)` now fails.** In `fastapi/openapi/utils.py`, `list(routes or [])` became `list(routes)`.
   - **Base:** returns `{}`.
   - **Head:** `TypeError: 'NoneType' object is not iterable`.
   - **Note:** the parameter is typed as required, so this break is minor.
   - **Probe:** `p14_get_openapi_none.py`

8. **Requests to included routes are slower.** `APIRoute.handle` now rebuilds `request_response(self.get_route_handler())` on every request. Matching also runs twice per nesting level: once in `matches` and again in `_handle_selected`.
   - **Result (µs per request, base then head):**
     - one-level include: 109/80 on base, 194/130 on head
     - 4-level nest with 20 routes each: 272/164 on base, 715/542 on head
   - **Contract broken:** the updated docs say inclusion is "designed to avoid adding overhead to each request".
   - **Note:** these are timings on one machine, so how much it matters depends on scale.
   - **Probes:** `p30_perf.py`, `p31_perf_single.py`

9. **A mount added after the first request stays unreachable.** This comes from the `_IncludedRouter.effective_candidates` cache: `Router.mount` (and `host`) never call `_mark_routes_changed`.
   - **Trigger:** `r.mount("/m2", ...)` after `r` is included and has served a request.
   - **Base:** mounts in included routers were never supported (404).
   - **Head:** a mount added before the first request returns 200; one added after returns 404.
   - **Contract broken:** the release notes promise live inclusion. This is a gap in the new feature, not a regression from base.
   - **Probe:** `p07_late_mount_and_ws.py`

## Dropped leads (counterevidence)

- **Merging of options across include levels:** prefix, tags, dependencies (and their order), responses, deprecated, `include_in_schema`, `default_response_class`, `generate_unique_id_function` and `strict_content_type` were tested together over two nested levels. Base and head are identical (`p23_combos.py`).
- **Redirect slashes and 405 with the `Allow` header:** identical on base and head (`p06`).
- **One router included twice:** `url_for`, `url_path_for` and the distinct operationIds match base (`p12`).
- **Dependency overrides on nested includes:** work on head. A router included after the app include now also works, which base did not support (`p13`).
- **WebSocket in an included router:** works the same on base and head (`p07`).
- **Iterating `app.routes` as a flat list of `APIRoute`** (for example the old `use_route_names_as_operation_ids` recipe, or code reading `route.path`): the release notes list this as a breaking change and the docs were updated, so I did not treat it as a defect.
- **New assert against cyclic includes (`_contains_router`):** it prevents infinite recursion in the live tree, which is intended.
- **Routes version as a sum of counters:** versions only increase, so the sum cannot repeat a value through the public API.
- **Host route with an empty prefix:** base raised `AttributeError` here and head fixes it, so it is an improvement.
- **The new `scope["fastapi"]` key and its leftover context:** every use checks object identity (`original_route is self`), so mounted sub-apps are unaffected.