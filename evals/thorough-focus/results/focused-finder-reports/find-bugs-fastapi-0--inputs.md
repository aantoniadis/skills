I found 10 candidates I could not contradict. One read, no workers. I compared base `016ab760` with head `1e70f7cd` using the locked venv, with `PYTHONPATH` set to the base worktree or the head checkout. The checkout is unchanged (`git status` is clean, HEAD is still `1e70f7cd`) and the base worktree has been removed.

All probes are in `<scratch>/out-arm/find-bugs-fastapi-0/.scratch/router-tree/search-1/finder-inputs/probes/`. To run one on both sides: `probes/run.sh probes/<pNN>.py`. Each `<pNN>.out` file holds the exact command and the output for both sides.

## Candidates (none contradicted)

**1. Nested `APIRoute` with an empty path is wrongly rejected** (`fastapi/routing.py:1614`, used at `:2438`)
- **Trigger:** router C has `@c.get("")`, `b.include_router(c, prefix="/c")`, then `app.include_router(b)` with no prefix.
- **Base:** the include works and `GET /c` returns 200.
- **Head:** `FastAPIError: Prefix and path cannot be both empty (path operation: root)`.
- **Contract broken:** a valid nested include that worked before now fails. `_iter_included_route_candidates` yields the original, unprefixed `APIRoute` (its `starlette_route` is None), so the empty-path check looks at `""` instead of `/c`.
- **Probe:** p02_nested_empty_path, executed.

**2. `scope["route"]` lost the include prefix and include metadata** (`routing.py:1593`, plus `APIRoute.matches` at `:1162`)
- **Trigger:** a middleware reads `request.scope["route"].path` (or `.tags`) for a route in a router included with a prefix. This is how tracing and metrics tools get the route template.
- **Base:** `'/v1/items/{item_id}'`, tags `['v1','items']`.
- **Head:** `'/items/{item_id}'`, tags `['items']`.
- **Contract broken:** `scope["route"]` should describe the matched operation. Route templates in traces and metrics become wrong and collide across prefixes. The release notes do not mention it.
- **Probe:** p01_scope_route_path, executed.
- **Same cause, inferred:** a custom `APIRoute.get_route_handler` that reads `self.path` or `self.dependencies` now sees the unprefixed state.

**3. A preset `app.openapi_schema` is silently regenerated** (`fastapi/applications.py:1083-1084`)
- **Trigger:** assign `app.openapi_schema = {...}` without overriding `app.openapi`.
- **Base:** `/openapi.json` serves the custom schema (`info.title` is `custom`).
- **Head:** `_openapi_routes_version` is None, so the cache check fails and the schema is replaced with the generated one (`title` is `FastAPI`).
- **Probe:** p03_openapi_schema_preset, executed.

**4. Callbacks from a callback router that includes another router are dropped from OpenAPI** (`fastapi/openapi/utils.py:325`)
- **Trigger:** `callbacks=cb.routes`, where `cb.include_router(inner)`.
- **Base:** `callbacks: {'ev': {...}}`.
- **Head:** `callbacks: {}`. The loop keeps only `isinstance(callback, APIRoute)` and skips the `_IncludedRouter` entries.
- **Contract broken:** the documented callbacks feature.
- **Probe:** p05_callback_router_nested, executed.

**5. `generate_unique_id_function` now receives `_EffectiveRouteContext`, not the route instance** (`routing.py:985`, via `from_api_route` at `:1332`)
- **Trigger:** a custom function that checks `isinstance(route, APIRoute)` or reads an attribute of an `APIRoute` subclass.
- **Base:** called with `MyRoute /p/a`, operationId `special-a`.
- **Head:** called with `_EffectiveRouteContext /p/a`, operationId `NOTAPIROUTE-a`. Reading the subclass attribute would raise `AttributeError`.
- **Contract broken:** the parameter is typed `Callable[[APIRoute], str]`, and the edited docs say "The function receives each `APIRoute`".
- **Probe:** p06_unique_id_fn_arg, executed.

**6. Errors in include-level configuration moved from include time to every request** (`routing.py:1431` `effective_candidates`, built lazily)
- **Trigger:** `app.include_router(r, responses={204: {"model": M}})`.
- **Base:** `AssertionError: Status code 204 must not have a response body` at include time, so startup fails.
- **Head:** the include succeeds. Every request returns 500 (seen 2 of 2) and `/openapi.json` returns 500. The cache is never stored because the build raises each time.
- **Probe:** p16_deferred_validation, executed.

**7. Plain Starlette routes in nested routers moved to a different URL** (`routing.py:1461` and `:1487`; `for_include` prefix is `parent_router.prefix + prefix`)
- **Trigger:** `c.add_route("/plain", ...)`, `b = APIRouter(prefix="/b")`, `b.include_router(c, prefix="/c")`, `app.include_router(b)`.
- **Base:** `/c/plain` returns 200 and `/b/c/plain` returns 404. The base `Router.add_route` ignored the router prefix.
- **Head:** `/c/plain` returns 404 and `/b/c/plain` returns 200.
- **Contract broken:** a URL change for existing apps that the release notes do not mention. Head is arguably more consistent with how `APIRoute` paths are built, so this one is for the maintainers to decide.
- **Probe:** p07_starlette_route_nested_prefix, executed.
- **Same cause, inferred:** `add_websocket_route` in a nested router with a prefix. To settle it, run p07 with a websocket route.

**8. Route handler rebuilt on every request for included routes** (`routing.py:1180`)
- **Trigger:** any request to an `APIRoute` inside an included router.
- **Base:** 0 calls to `get_route_handler` over 5 requests.
- **Head:** 5 calls.
- **Contract broken:** side effects in a custom `get_route_handler` repeat on every request, and each request pays the handler build. The edited docs say inclusion is "designed to … avoid adding overhead to each request".
- **Probe:** p09_handler_per_request, executed.

**9. Code that looks up route templates over `app.routes` breaks** (`_IncludedRouter` has no `.path`)
- **Trigger:** the pattern instrumentation libraries use: `for r in app.routes: if r.matches(scope)[0] == Match.FULL: r.path`.
- **Base:** `APIRoute /items/{i}`.
- **Head:** `AttributeError: '_IncludedRouter' object has no attribute 'path'`.
- **Status:** the release notes declare `router.routes` a tree, so this is a known break. The consumer impact is the open question.
- **Probe:** p14_routes_consumers, executed.

**10. `get_openapi(routes=None)` now raises** (`fastapi/openapi/utils.py:562`, previously `routes or []`)
- **Base:** returns `{}`.
- **Head:** `TypeError: 'NoneType' object is not iterable`.
- **Status:** weak. `routes` is typed as a required `Sequence`, so None was never a documented input.
- **Probe:** p04_get_openapi_routes_none, executed.

## Dropped leads
- **Option combinations:** a nested matrix of 1024 combinations produced byte-identical OpenAPI output and responses on base and head (p13_option_matrix, p13_base.json vs p13_head.json; same sha `27bb42e4`). It covered:
  - `default_response_class` at router C, router B and the include call
  - `generate_unique_id_function` at C, B and the app
  - include-level dependencies
  - `include_in_schema`
  - `deprecated`
  - `strict_content_type`
  - tags and responses
- **Router-level options:** router-level `dependencies`, `callbacks`, `responses` and `deprecated`, plus app-level dependencies, gave identical dependency order and OpenAPI output (p15).
- **Routing basics:** `url_for` with the same router included twice, the redirect-slashes 307 and 405 with its `Allow` header are all identical (p10).
- **Dependency overrides:** `dependency_overrides` and include dependencies behave the same for HTTP and WebSocket routes (p12).
- **Late child include:** a child router included after its parent was already included still runs its startup handler on head, same as base (p08). The routes now work on head, matching the new docs.
- **Mounts:** a Mount inside an included router is now served (base returned 404). This is new and intended behavior (p11).
- **Hashability:** `set(app.routes)` is unhashable on base too, because Starlette `Route` defines `__eq__` (p14).
- **Version-sum cache:** the routes version sum only increases through the API, and cycles are blocked by the `_contains_router` assert. A stale cache needs direct `routes` mutation or `mount()` after a first build, neither of which base supported.
- **Shared scope key:** `scope["fastapi"]` state in nested or mounted apps is protected by the `original_route is self` and `original_router is self` identity checks.