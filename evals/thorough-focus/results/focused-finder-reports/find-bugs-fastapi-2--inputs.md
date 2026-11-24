I found 10 candidates I could not contradict; 9 have a saved probe and one (C10) is inferred from the source, with the probe to run. I searched alone, in one read, and started no workers. The probes are in `<scratch>/out-arm/find-bugs-fastapi-2/.scratch/router-tree/search-1/finder-inputs/probes/`. To repeat one, run `./run.sh <probe.py>` from that folder: it runs the probe on a base worktree at 016ab76, then on the head checkout, with `PYTHONPATH` set. The commands are in `COMMANDS.txt` there, and the results for p1–p10 are in `results.txt`. I removed the base worktree afterwards, and `git status` on the checkout is clean.

## Candidates

**C1. Included routes expose the original route in `scope["route"]`, with no prefix, tags or dependencies from the include**
- **Location:** `fastapi/routing.py:1593` (`scope["route"] = original_route`) and `:1162` (`child_scope["route"] = self`).
- **Trigger:** any included router with a prefix, tags or dependencies, read through `request.scope["route"]`. Middleware and instrumentation such as Sentry or OpenTelemetry read this for the path template.
- **Base:** `path='/api/items/{item_id}'`, `tags=['inc','r']`, one dependency.
- **Head:** `path='/items/{item_id}'`, `tags=['r']`, no dependencies. HTTP middleware sees the same values.
- **Contract:** `scope["route"]` stops describing the route that served the request. The release notes declare only `router.routes` as changed.
- **Probe:** `p3_scope_route_path.py`

**C2. A route with an empty path in a nested router is now rejected**
- **Location:** `fastapi/routing.py:2438`. `_iter_included_route_candidates` yields the original `APIRoute`, whose path has no prefix, while Starlette routes are yielded with their prefix.
- **Trigger:** router B has `@b.get("")`, A runs `include_router(b, prefix="/b")`, then the app runs `include_router(a)` with no prefix.
- **Base:** the include works, and `GET /b` returns 200.
- **Head:** `FastAPIError: Prefix and path cannot be both empty (path operation: root_b)`.
- **Contract:** a valid route tree that base accepted is now rejected.
- **Probe:** `p1_empty_prefix_nested.py`

**C3. `app.openapi()` overwrites an `app.openapi_schema` the user set**
- **Location:** `fastapi/applications.py:1083-1084`. `_openapi_routes_version` starts as `None`, so it never equals the current routes version.
- **Trigger:** setting `app.openapi_schema = {...}` without replacing `app.openapi`.
- **Base:** `app.openapi()` and `/openapi.json` return the custom schema (title "custom").
- **Head:** both regenerate the schema (title "FastAPI").
- **Contract:** a schema set on the documented cache attribute was honoured before and is now silently discarded.
- **Probe:** `p2_openapi_schema_preset.py`

**C4. `get_openapi(routes=None)` raises `TypeError`**
- **Location:** `fastapi/openapi/utils.py:562` (`list(routes)`), and the loop that follows, which iterates `_iter_routes_with_context(routes)`.
- **Trigger:** `get_openapi(title=..., version=..., routes=None)`.
- **Base:** returns a schema with `paths: {}`.
- **Head:** `TypeError: 'NoneType' object is not iterable`.
- **Contract:** base handled `None` with `routes or []`. The type hint says a sequence is required, so this is a minor break.
- **Probe:** `p4_get_openapi_none.py`

**C5. Callback operations from a router nested inside a callback router disappear from OpenAPI**
- **Location:** `fastapi/openapi/utils.py:326`. Only `isinstance(callback, routing.APIRoute)` is kept, so `_IncludedRouter` entries are skipped. `get_fields_from_routes` does traverse them, so their models still reach the schema components.
- **Trigger:** `cb_router.include_router(inner)`, then `callbacks=cb_router.routes`.
- **Base:** callbacks `['cb_event', 'cb_invoice']`.
- **Head:** callbacks `['cb_invoice']`.
- **Contract:** the documented `callbacks=router.routes` pattern no longer documents every callback.
- **Probe:** `p5_callbacks_nested.py`

**C6. A custom `route_class` that wraps `self.app` in `__init__` is bypassed for included routes**
- **Location:** `fastapi/routing.py:1180`. For included routes, `APIRoute.handle` builds `request_response(self.get_route_handler())` on every request and ignores `self.app`.
- **Trigger:** a subclass sets `self.app = wrapper(self.app)` after `super().__init__`, and its router is included.
- **Base:** the wrapper runs (`calls=['/api/w']`).
- **Head:** the wrapper never runs (`calls=[]`). A route declared directly on the app would still use `self.app`.
- **Contract:** the head docs say custom `APIRoute` subclasses "can still participate" after inclusion.
- **Probe:** `p6_route_subclass_app_wrap.py`

**C7. Attributes a custom `route_class` sets in `__init__` are lost after inclusion**
- **Location:** `fastapi/routing.py:1340`. `_EffectiveRouteContext.from_api_route` rebuilds the route state through `_populate_api_route_state`, and `_EffectiveRouteContext.matches` (about lines 1385-1395) uses its own `path_regex`.
- **Trigger:** the subclass recompiles `self.path_regex` with `re.IGNORECASE`. The same applies to any `__init__` change to `dependant`, `path_regex` or similar fields.
- **Base:** `/api/hello` returns 200 and `/api/Hello` returns 200.
- **Head:** `/api/hello` returns 404 and `/api/Hello` returns 200.
- **Contract:** the same as C6. Base re-ran the subclass `__init__` through `route_class_override`.
- **Probe:** `p7_route_subclass_init_mutation.py`

**C8. `generate_unique_id_function` receives a non-`APIRoute` object for included routes**
- **Location:** `fastapi/routing.py:985`, called with an `_EffectiveRouteContext` dataclass.
- **Trigger:** a custom function that checks `isinstance(route, APIRoute)`, or reads a subclass-only attribute such as `x_type`.
- **Base:** `isinstance` is always `True`.
- **Head:** `isinstance` is `False` for included routes. Operation IDs are identical in this probe. A function that reads a subclass attribute would raise `AttributeError` at include time; this is *inferred*, and the probe to run is to read `getattr(route, "x_type")` inside the function.
- **Contract:** the head docs at `path-operation-advanced-configuration.md` say "The function receives each `APIRoute`".
- **Probe:** `p12_misc.py`, last line.

**C9. Including a router that already includes the parent now fails**
- **Location:** `fastapi/routing.py:2428`.
- **Trigger:** `a.include_router(b)`, then `b.include_router(a)`.
- **Base:** works, because the routes were copied as they were at include time.
- **Head:** `AssertionError: Cannot include an APIRouter instance that already includes this router`.
- **Contract:** a sequence base accepted now fails. It is unusual and may be intended; the author decides.
- **Probe:** `p9_cycle.py`

**C10. Included routes cost about 60% more per request**
- **Location:** `fastapi/routing.py:1180`, which rebuilds the handler on every request. Matching also runs twice (`_IncludedRouter.matches`, then `_handle_selected` calls `_match` again), and `_get_routes_version` walks the router tree on each `effective_candidates()` call.
- **Trigger:** any request to an included route. The probe had 50 sibling routes and called the app over raw ASGI.
- **Base:** 216 µs per request.
- **Head:** 349 µs per request.
- **Contract:** the head docs say inclusion is designed "to avoid adding overhead to each request". Whether this matters depends on traffic scale.
- **Probe:** `p14_per_request_cost.py`. This is one run on one machine with no repeated runs, and I have not split the cost between the three causes.

## Dropped leads
- **`include_router` options, alone and combined:** `prefix`, `tags`, `dependencies`, `default_response_class`, `responses`, `callbacks`, `deprecated`, `include_in_schema` and `generate_unique_id_function`, on the outer and inner include, crossed with 9 router-level settings. That is 900 combinations, comparing the OpenAPI output and GET/POST results, including a POST with a `text/plain` content type to exercise `strict_content_type`. Base and head were identical (`p11_result.txt`: "differing: 0").
- **Request behaviour through nested includes:** dependency overrides (HTTP and websocket), websocket dependencies, Starlette `add_route`, `redirect_slashes`, HEAD and 405 with the `Allow` header, `url_for` and `app.url_path_for`. All identical (`p12_result.txt`).
- **Routes, routers and mounts added after inclusion:** head serves and documents them; base returned 404. This is the intended feature (`p13_result.txt`). The `mount()` call does not bump the routes version, but base never routed mounts inside included routers, so head is not worse.
- **Lost stream item type for an included JSONL endpoint:** extra fields pass through unchanged at both base and head (`p8_stream_item_included.py`), so this is pre-existing.
- **Router `on_startup` with a nested include made after the app include:** works at both; head also fixes base's 404 (`p10_nested_startup_after_include.py`).
- **`router.routes` is no longer flat, and the old operation-ID tutorial mutated `app.routes`:** both are declared as breaking changes in the release notes.
- **Stale or shared `scope["fastapi"]` keys:** matching restores the keys, and every reader checks `original_router is self` or `original_route is self`, so I found no reachable mix-up.
- **ContextVar in `get_route_handler`:** it is set and reset synchronously around the build, so requests cannot interleave there.
- **Route versions that never change, or two different trees summing to the same version:** each router's version only grows and only documented APIs change it; direct mutation of `router.routes` is warned against in the docs.
- **Hosts in included routers:** base raised `AttributeError` on a Host's missing path when no prefix was given; head handles them, so this is not a regression.