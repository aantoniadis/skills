I found seven candidates I could not contradict. I ran each one at base 016ab76 and head 1e70f7c, so all are executed, none inferred. This was one read, with no workers.

The lead's static deltas, `weakened_checks.py` and base test run were left to the lead. The base worktree has been removed, and the checkout is clean at 1e70f7c.

Probe folder: `<scratch>/out-arm/find-bugs-fastapi-2/.scratch/router-tree/search-1/finder-general/probes/`
- Scripts: `probe_all.py` (scenarios p1–p10) and `probe_more.py` (scenarios q1–q5).
- Logs: `probe_all.base.log`, `probe_all.head.log`, `probe_more.base.log`, `probe_more.head.log`. Each log starts with its exact command and with the path FastAPI was loaded from, which confirms the right checkout ran.
- Command: `PYTHONPATH=<checkout> /tmp/real-pr-cache/fastapi/venv/bin/python probe_all.py` (or `probe_more.py`).

## Candidates

1. **`scope["route"]` for an included route is now the original, unprefixed route.**
   - **Location:** `fastapi/routing.py:1593` in `_IncludedRouter._handle_selected` (`scope["route"] = original_route`), and `APIRoute.matches` at about line 1162.
   - **Trigger:** `app.include_router(router, prefix="/api/v1", tags=["t"])`, then reading `request.scope["route"]` in an endpoint or in middleware.
   - **Base:** `path='/api/v1/items/{item_id}'`, `tags=['t']`.
   - **Head:** `path='/items/{item_id}'`, `tags=[]`.
   - **Middleware check (p1b):** base logs `/api/v1/items/{item_id}`; head logs `/items/{item_id}`.
   - **Contract broken:** `scope["route"]` should describe the route that actually ran. Metrics and tracing middleware group requests by the route template, so they now report unprefixed templates, and routes that share a path under different prefixes fall into one group. The release notes list only `router.routes` as a breaking change.
   - **Probe:** p1 and p1b.

2. **An `openapi_schema` assigned directly is thrown away; edits made after `app.openapi()` are lost.**
   - **Location:** `fastapi/applications.py:1083-1084`. `_openapi_routes_version` starts as `None`, so it never equals the router's version until FastAPI builds the schema itself.
   - **Trigger (p2):** set `app.openapi_schema = {...custom...}`, then request `/openapi.json`.
     - Base returns the custom schema (title `CUSTOM`).
     - Head rebuilds it (title `FastAPI`).
   - **Trigger (p2b):** call `schema = app.openapi()`, change `schema["info"]` in place, then include another router.
     - Head drops the edit (`x-logo kept: False`).
     - Base kept the edit but did not show the new route.
   - **Contract broken:** `openapi()` used to return a cached schema the user set or edited. Now any route-version mismatch silently overwrites it.

3. **A callbacks router that includes a sub-router loses its callbacks in OpenAPI.**
   - **Location:** `fastapi/openapi/utils.py:326`. The callback loop keeps only `isinstance(callback, routing.APIRoute)`, so `_IncludedRouter` entries in `cb_router.routes` are skipped. The field collection in `get_fields_from_routes` does walk the tree, so the two disagree.
   - **Trigger:** `cb_router.include_router(cb_sub)`, then `@app.post(..., callbacks=cb_router.routes)`.
   - **Base:** `callbacks` contains `cb_notify`.
   - **Head:** `callbacks` is `{}`.
   - **Contract broken:** the edited docs (openapi-callbacks.md) still say to pass `.routes` and that FastAPI will generate the callback docs from them.
   - **Probe:** p3.

4. **What a custom `APIRoute` subclass does in `__init__` is lost for included routes.**
   - **Location:** `_EffectiveRouteContext.from_api_route` (routing.py:1332) rebuilds state with `_populate_api_route_state`, and `APIRoute.handle` (routing.py:1180) builds `request_response(self.get_route_handler())` and ignores `self.app`. Base re-created each route with `route_class_override=type(route)`, which ran `__init__` again.
   - **Trigger (p4):** a subclass adds a dependency to `self.dependant` after `super().__init__()`.
     - Base runs the dependency (`['dep']`).
     - Head does not (`[]`).
   - **Trigger (p4b):** a subclass wraps `self.app` to block requests with a header.
     - Base returns 403.
     - Head returns 200: the guard is bypassed.
   - **Contract broken:** the edited bigger-applications.md says custom `APIRoute` subclasses "can still participate after the router is included".

5. **`generate_unique_id_function` now receives an `_EffectiveRouteContext`, not the route-class instance.**
   - **Location:** routing.py:985, `current_generate_unique_id(route)`, where `route` is the context.
   - **Trigger:** `FastAPI(generate_unique_id_function=gen)` with a router using a custom `route_class` that has an attribute such as `x_type`.
   - **Base:** `gen` sees `XRoute`, and the operationId is `x_X`.
   - **Head:** `gen` sees `_EffectiveRouteContext`, and the operationId is `x_NOATTR`.
   - **Contract broken:** the function is typed and documented (in the new docs_src tutorial002) as receiving an `APIRoute`. An `isinstance` check or a subclass attribute now fails, which silently changes operationIds and client code generated from them.
   - **Probe:** p7.

6. **Configuration errors from `include_router` now appear only at request time, as 500s.**
   - **Location:** `_IncludedRouter.effective_candidates` and `_build_effective_context` (routing.py:1431 and 1452) build contexts lazily, at the first request or schema build.
   - **Trigger (p6):** `include_router(router, responses={204: {"model": Item}})`.
     - Base raises `AssertionError` at `include_router` (at startup).
     - Head's `include_router` succeeds and `GET /x` returns 500.
   - **Trigger (p6b):** `include_router(..., dependencies=[Depends(dep)])`, where `dep` declares the path parameter `item_id` with `Query()`.
     - Base raises at include.
     - Head returns 500 on the request.
   - **Extra effect:** a failed build resets `_effective_candidates` without updating the version, so every request retries the build and fails again.
   - **Contract broken:** startup used to reject bad configuration; now it passes deploy and fails in production.

7. **Plain Starlette routes in nested prefixed routers move to a different URL.**
   - **Location:** routing.py:1230. `for_include` uses `prefix=parent_router.prefix + prefix`, and `path_for` now applies it to `routing.Route` and `WebSocketRoute`. Base used `add_route`, which never added the parent router's prefix.
   - **Trigger:** `inner.add_route("/plain", ...)`, then `APIRouter(prefix="/outer").include_router(inner, prefix="/inner")`, then `app.include_router(outer)`.
   - **Base:** `/inner/plain` returns 200 and `/outer/inner/plain` returns 404.
   - **Head:** the reverse.
   - **Contract broken:** the URL changes silently and the release notes do not mention it. You may decide the head behaviour is the intended fix; the old URL still breaks for existing clients.
   - **Probe:** p5.

## Dropped leads

- **`app.routes` contains `_IncludedRouter` (p10):** the release notes document this as a breaking change.
- **Cost of `get_route_handler` per request (routing.py:1180):** `get_request_handler` only builds closures, so the cost is small.
- **Double or recursive matching (`_IncludedRouter.matches`, then `_handle_selected` re-matching):** this costs performance only; behaviour is correct.
- **Mount added after the first request returns 404 (q5):** base also returns 404, because base never included Mounts.
- **Nested `url_for` (p8):** same on base and head.
- **Dependency overrides through a nested include (p9):** same on base and head.
- **Redirect-slashes and 405 `Allow` header (q1):** same on base and head.
- **WebSocket dependencies from an outer router (q2):** same on base and head.
- **Same router included twice (q3):** same on base and head.
- **Route added after a request (q4):** now works on head; it was 404 on base, so this is an improvement.
- **Inheritance of response class, tags, dependencies, callbacks, unique-id function and `strict_content_type`:** I traced the combine order in `for_include`, `combine` and `from_api_route`; it matches base precedence.
- **`stream_item_type` not re-derived for included routes:** base also passed the already-resolved `response_model`, so this is not new.
- **`_IncludedRouter` dataclass eq/unhashable:** I found no in-repo code that hashes or compares routes.
- **`get_openapi` dropped `routes or []`:** `routes` is a required `Sequence` parameter.
- **Cycles in `_get_routes_version`:** the new `_contains_router` assertion prevents them, and diamond-shaped includes are deduplicated by the `seen` set.