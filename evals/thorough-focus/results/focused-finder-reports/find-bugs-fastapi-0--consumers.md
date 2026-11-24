I found 8 candidates where code outside the change sees something different at base 016ab760 and head 1e70f7cd. Seven were run at both commits. The eighth (translated docs) is inferred. The reviewed checkout is unchanged at 1e70f7cd. The base worktree I created has been removed.

**Where things are:**
- Probes and their saved output: `<scratch>/out-arm/find-bugs-fastapi-0/.scratch/router-tree/search-1/finder-consumers/probes/`. Each `pN_*.py` has a `pN_*.out` beside it.
- To re-run one, use `probes/run.sh pN_x.py` from that folder. It runs the probe at base (from `../base`, so recreate that worktree first) and at head. It uses `/tmp/real-pr-cache/fastapi/venv/bin/python` with PYTHONPATH set to each checkout.
- `p10_run.sh` runs `mypy --strict` the same way, with MYPYPATH instead of PYTHONPATH.

## Candidates

**1. `request.scope["route"]` is now the original route, without the include's prefix, tags or dependencies.**
- **Location:** `fastapi/routing.py`, `_IncludedRouter._handle_selected` (`scope["route"] = original_route`) and `APIRoute.matches` (`child_scope["route"] = self`).
- **Trigger:** `app.include_router(router, prefix="/v1", tags=["v1"])` where `router` has prefix `/items`. Middleware or a dependency then reads `scope["route"]`.
- **Base:** path and path_format are `/v1/items/{item_id}`; tags are `['v1','items']`.
- **Head:** path and path_format are `/items/{item_id}`; tags are `['items']`.
- **Instrumentation pattern:** code that loops over `app.routes`, calls `route.matches(scope)` and reads `route.path` (prometheus-fastapi-instrumentator does this) now matches `_IncludedRouter`, which has no `.path`. That raises AttributeError.
- **Contract broken:** the route template that middleware reports (metrics and tracing labels) changes for every included route. `scope["route"]` is not covered by the release-note warning, which only says iterating `router.routes` breaks.
- **Probe:** `p1_scope_route.py`.

**2. A schema the user assigns to `app.openapi_schema` is silently overwritten.**
- **Location:** `fastapi/applications.py` `FastAPI.openapi`: `if not self.openapi_schema or self._openapi_routes_version != routes_version`, where `_openapi_routes_version` starts as `None`.
- **Trigger:** assign `app.openapi_schema = {...}` (for example, loaded from a file), then call `app.openapi()` or request `/openapi.json`.
- **Base:** the assigned schema is returned.
- **Head:** a schema is generated and replaces it ("preset survives: False").
- **Related:** if a user edits the dict that `app.openapi()` returned (say, adds an `x-logo`) and then adds a route, the edit is lost at head. That part may be intended invalidation.
- **Contract broken:** `openapi()` used to return any schema already set; it now ignores it.
- **Probe:** `p2_openapi_schema_preset.py`.

**3. A parent `APIRouter` subclass's `add_api_route` (and `add_route` / websocket) overrides no longer run for included routes.**
- **Location:** `APIRouter.include_router` now appends `_IncludedRouter` instead of calling `self.add_api_route(...)`.
- **Trigger:** a `SlashRouter(APIRouter)` that overrides `add_api_route` to also register `/x` next to `/x/`, then `parent.include_router(child)`.
- **Base:** the override sees `['/items/']`; `GET /api/items` returns 200.
- **Head:** the override sees `[]`; `GET /api/items` returns 307.
- **Contract broken:** a subclass hook that every included route used to pass through is no longer called.
- **Probe:** `p3_router_subclass_override.py`.

**4. Callbacks from a router included into a callback router disappear from OpenAPI.**
- **Location:** `fastapi/openapi/utils.py` `get_openapi_path`. The callbacks loop still filters with `isinstance(callback, routing.APIRoute)` and does not walk the route tree, while `get_fields_from_routes` does walk it.
- **Trigger:** `callback_router.include_router(events_cb)`, then `@app.post(..., callbacks=callback_router.routes)`. This is the pattern in the openapi-callbacks docs.
- **Base:** the `on_event` callback is in `operation["callbacks"]`.
- **Head:** `callbacks: {}`, while the `Event` model still appears in components.
- **Contract broken:** the callbacks feature and its documentation.
- **Probe:** `p5_callbacks_nested.py`.

**5. A user's `generate_unique_id_function` gets a `_EffectiveRouteContext`, not an `APIRoute`.**
- **Location:** `_EffectiveRouteContext.from_api_route` → `_populate_api_route_state` → `current_generate_unique_id(route)`.
- **Trigger:** `FastAPI(generate_unique_id_function=gen)` with an included router whose `route_class` is a subclass carrying extra attributes.
- **Base:** `gen` receives `VersionedRoute` (`isinstance(route, APIRoute)` is True); operationId is `v2_get_x`.
- **Head:** `gen` receives `_EffectiveRouteContext` (isinstance is False); operationId is `MISSING_get_x`.
- **Contract broken:** the parameter is typed `Callable[[APIRoute], str]`, and the new docs example annotates `route: APIRoute`.
- **Probe:** `p6_unique_id_fn_arg.py`.

**6. Custom `APIRoute` subclass hooks behave differently for included routes.**
- **Location:** `APIRoute.handle` builds `request_response(self.get_route_handler())` on every request; `from_api_route` does not call the subclass's `__init__`.
- **`__init__` not re-run:**
  - **Base:** `__init__` runs a second time with the full path and the include's tags. The registry holds `['/users', '/admin/users']`, and the tag-driven auth dependency the subclass injects applies (422 without the header).
  - **Head:** the registry holds `['/users']`, and `GET /admin/users` returns 200 with no key, so the subclass's injected auth is skipped.
- **`get_route_handler` per request:**
  - **Base:** called 2 times in total.
  - **Head:** called once at setup plus once for every request (6 after 5 requests).
- **Contract broken:** the updated bigger-applications docs say custom `APIRoute` subclasses "can still participate" after inclusion. A `get_route_handler` override with setup cost or side effects now runs on every request.
- **Raw speed:** I measured no per-request overhead for the default class (see dropped leads).
- **Probes:** `p8_route_subclass_init.py`, `p7_route_handler_per_request.py`.

**7. To a type checker, `APIRoute` no longer has its documented attributes.**
- **Location:** `APIRoute.__init__` now sets attributes through `_populate_api_route_state(cast(_APIRouteLike, self), ...)`, and the class declares none of them.
- **Trigger:** user code (or the generate-clients docs pattern `route.tags[0]`) that reads `route.tags`, `.unique_id`, `.operation_id`, `.summary`, `.response_model` or `.dependant`, checked with `mypy --strict`.
- **Base:** "Success".
- **Head:** 6 `attr-defined` errors, for example `"APIRoute" has no attribute "tags"`.
- **Contract broken:** FastAPI's public type declarations.
- **Probe:** `p10_typing_consumer.py`, run by `p10_run.sh`.

**8. The translated docs (inferred) still describe the removed pattern and point at highlight lines that no longer exist.**
- **Location:** `docs/{de,ja,ko,es,zh-hant,ru,uk,fr,tr,pt}/docs/advanced/path-operation-advanced-configuration.md`. Each says to iterate `app.routes` and set `operation_id`, with `hl[2, 12:21, 24]` on `tutorial002_py310.py`, which is now 14 lines.
- **Trigger:** viewing any translated page.
- **Base:** the text and highlights match the example.
- **Head:** the text and highlights refer to code that is gone, and the advice no longer reaches included routes.
- **Caveat:** FastAPI usually updates translations later, by automation.
- **Probe to run:** build one translated page, or grep (already done) and compare with `wc -l` = 14.

**Wider case of the release-note breaking change (you decide):** Starlette's `SchemaGenerator.get_endpoints(app.routes)` returns no included routes at head, versus `['/v1/o/x/{n}', '/v1/o/in/i/{n}']` at base. The release notes already say that iterating `router.routes` breaks, so this is mainly a question of intent. Probe: `p9_url_for.py`.

## Dropped leads
- **`app.url_path_for` / `request.url_for` on nested includes:** identical at base and head (`p9_url_for.py`).
- **Per-request overhead for included routes (default route class):** 269 vs 258 µs per request at head, and base was noisier (345/278), so no regression (`p7b_request_overhead.py`).
- **An `APIRouter` mounted as an ASGI app that contains an include, and one router shared between two apps with per-app `dependency_overrides`:** identical results (`p11_router_as_asgi.py`).
- **`router.mount()` / `host()` don't bump `_routes_version`, so a Mount added after the first request is cached out:** base never routed Mounts or Hosts from included routers at all, so this is not a regression. It does contradict the release note's "adding routes after include works".
- **Unhashable `_IncludedRouter` (a dataclass with eq):** Starlette `Route` already defines `__eq__` and is unhashable, so sets of routes already failed at base.
- **Mutating route attributes after inclusion is not reflected:** base clones ignored those mutations as well.
- **Inheritance order of tags, dependencies, responses, `default_response_class`, `generate_unique_id_function` and `strict_content_type` across nested includes:** reading the code, `for_include`/`combine`/`from_api_route` resolve them in the same order as base's chained `add_api_route`.
- **Plain Starlette `Route` rebuilt without its `middleware=`:** base `add_route` dropped it too.
- **The empty-prefix check runs only at include time, so routes added later skip it:** base didn't register later routes at all; low value, not probed.
- **Stale `scope["fastapi"]` keys leaking into a mounted sub-app:** every reader compares by identity (`original_route is self`, `original_router is self`), so a stale key causes no misrouting.