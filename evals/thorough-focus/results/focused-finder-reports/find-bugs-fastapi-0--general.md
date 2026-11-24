I did one read of base `016ab760` → head `1e70f7cd` and found eight candidates I could not contradict, all executed. I didn't run the static deltas, `weakened_checks.py` or the base test suite, since those are yours.

Probes are in `<scratch>/out-arm/find-bugs-fastapi-0/.scratch/router-tree/search-1/finder-general/probes/`, with each `<name>.py` next to its `<name>.out` and the base and head output in each `.out`. The command for every probe is `./run.sh probes/<name>.py`, run from `finder-general/`; `COMMANDS.txt` there gives the exact interpreter and PYTHONPATH. The base and head worktrees I used are removed and the checkout is unchanged.

## Candidates

**1. `scope["route"]` for an included route is the original route without the include prefix or tags.**
- **Location:** `fastapi/routing.py`, `_IncludedRouter._handle_selected` (`scope["route"] = original_route`, about line 1593), and `APIRoute.matches` (`child_scope["route"] = self`).
- **Trigger:** `APIRouter(prefix="/items")` with `/{item_id}`, included with `prefix="/v1", tags=["x"]`; then read `request.scope["route"]` in the endpoint, a middleware or an exception handler.
- **Base:** `path='/v1/items/{item_id}'`, `path_format='/v1/items/{item_id}'`, `tags=['x']`.
- **Head:** `path='/items/{item_id}'`, `path_format='/items/{item_id}'`, `tags=[]`. `url_for` is still correct.
- **Contract broken:** `scope["route"]` is what middleware and monitoring tools such as Sentry read to label a request by its route path. The release notes' breaking-change section covers only `router.routes`, not `scope["route"]`. The new tests show that keeping the original subclass instance there is intended, so whether this is a defect is for you to decide.
- **Probe:** `scope_route_path.py`

**2. A schema assigned to `app.openapi_schema` is overwritten.**
- **Location:** `fastapi/applications.py`, `FastAPI.openapi`. It regenerates whenever `_openapi_routes_version` differs, and that value starts as `None`.
- **Trigger:** set `app.openapi_schema = {...}` without overriding `app.openapi`, then call `app.openapi()` or GET `/openapi.json`. A second case: change the dict returned by `app.openapi()` in place, then add a route.
- **Base:** returns the assigned schema (title `custom`). In the second case the change to `x-logo` is kept.
- **Head:** regenerates and discards it (title `FastAPI`). In the second case the change is lost.
- **Contract broken:** `openapi_schema` was the cache that `openapi()` returned when it was set.
- **Probe:** `openapi_schema_preset.py`

**3. Errors in include-level configuration move from include time to request time and break unrelated routes.**
- **Location:** `_IncludedRouter.effective_candidates` and `_EffectiveRouteContext.from_api_route`. The route state is now built lazily, on the first match or OpenAPI call.
- **Trigger:** `app.include_router(router, responses={204: {"model": M}})`, with an app route declared after the include.
- **Base:** `include_router` raises `AssertionError: Status code 204 must not have a response body` at startup.
- **Head:** `include_router` succeeds. Then `/health` (an unrelated route) and `/openapi.json` both return 500 on every request.
- **Contract broken:** configuration should fail at startup, not take down every request.
- **Probes:** `include_responses_error_timing2.py`, `include_responses_error_timing.py`

**4. `generate_unique_id_function` receives an `_EffectiveRouteContext`, not the `APIRoute`.**
- **Location:** `_populate_api_route_state`, `current_generate_unique_id(route)`, when called from `from_api_route`.
- **Trigger:** a router with `route_class=TaggedRoute` (class attribute `x_type`), included with `generate_unique_id_function=lambda r: f"{r.x_type}_{r.name}"`.
- **Base:** the operation ID is `T_y`, and the function receives a `TaggedRoute` instance (`isinstance(..., APIRoute)` is True).
- **Head:** `AttributeError: '_EffectiveRouteContext' object has no attribute 'x_type'`, and `isinstance` is False. Because of candidate 3, this error surfaces at request time.
- **Contract broken:** the parameter is typed `Callable[[APIRoute], str]`.
- **Probes:** `gen_unique_id_arg2.py`, `gen_unique_id_arg.py`

**5. OpenAPI drops callbacks that come from a callback router which itself includes a router.**
- **Location:** `fastapi/openapi/utils.py`, `get_openapi_path`. The callback loop keeps only `isinstance(callback, routing.APIRoute)` and skips `_IncludedRouter`, while `get_fields_from_routes` does walk the tree.
- **Trigger:** `cb.include_router(sub)`, then `@app.post(..., callbacks=cb.routes)`.
- **Base:** `callbacks` contains `{'evt': {...}}`.
- **Head:** `callbacks: {}`.
- **Contract broken:** the documented `callbacks=router.routes` pattern (openapi-callbacks.md).
- **Probe:** `callback_router_nested.py`

**6. Changes an `APIRoute` subclass makes in `__init__` are lost for included routes.**
- **Location:** `_EffectiveRouteContext.from_api_route`. It rebuilds the dependant and fields from the endpoint and attributes, without running the subclass `__init__`. Base re-instantiated `type(route)`.
- **Trigger:** a subclass that inserts a denying dependency into `self.dependant` after `super().__init__`, included with a prefix.
- **Base:** 403.
- **Head:** 200, so the guard is skipped and the endpoint runs.
- **Contract broken:** the head docs say custom `APIRoute` subclasses "can still participate after the router is included".
- **Probe:** `subclass_init_custom.py`

**7. `get_route_handler` now runs on every request to an included route.**
- **Location:** `APIRoute.handle`, `app = request_response(self.get_route_handler())`, in the effective-context branch.
- **Trigger:** an `APIRoute` subclass overriding `get_route_handler`, included in an app, three requests.
- **Base:** 0 calls during the requests (it runs once, at construction).
- **Head:** 3 calls.
- **Effect:** a subclass that does one-time setup there, such as registering a metric, repeats it on every request. The raw cost is only about 2.1 µs per call, so this is not a performance issue.
- **Probe:** `route_handler_per_request.py`

**8. A nested router included after its parent is in the app serves routes, but its lifespan never runs.**
- **Location:** `APIRouter.include_router`. Lifespan and startup handlers are still merged only at include time.
- **Trigger:** `app.include_router(router)`, then `router.include_router(other)`, where `other = APIRouter(lifespan=...)`.
- **Base:** GET `/o` returns 404 (the old docs said to include before).
- **Head:** GET `/o` returns 200, and the lifespan events are `[]`.
- **Contract broken:** the new docs in bigger-applications.md say "You can do this before or after including `router` in the FastAPI app", but endpoints that depend on the nested lifespan state now run without it.
- **Probe:** `late_nested_include_lifespan.py`

## Dropped leads
- **Iterating `app.routes` no longer sees included `APIRoute`s** (affects the old `use_route_names_as_operation_ids` docs example and OTel-style `.path` reads): the release notes list this as an intended breaking change and the docs example was rewritten.
- **Dependency overrides through nested includes, websocket overrides, redirect_slashes, 405 with `Allow`, double include with distinct tags and IDs, path params in the prefix:** base and head give the same results (`misc_routing.py`).
- **Starlette `Route` `url_for` inside a nested prefixed router:** base 404, head correct. This is an improvement (`misc_routing.py`).
- **Streaming item type lost for included JSONL/SSE routes:** the output is identical at base, so it predates the change (`stream_item_included.py`).
- **`_IncludedRouter` is unhashable:** Starlette `Route` entries are already unhashable at base (`route_hash_and_handler_cost.py`).
- **Per-request handler rebuild as a performance cost:** about 2.1 µs per call, negligible.
- **Including a plain Starlette `Router`:** it fails at base too (`AttributeError: on_startup`) (`include_starlette_router.py`).
- **`get_openapi(routes=None)` now raises:** `routes` is typed as a required `Sequence[BaseRoute]`.
- **Ordering and merging of include metadata** (response class, deprecated, tags, dependencies, callbacks, `generate_unique_id_function`, `strict_content_type`), compared by reading `combine`/`for_include`/`from_api_route` against base `include_router` plus `add_api_route`: the order is the same.
- **The `fastapi` scope dict leaking through the shallow copy for redirects:** values are restored after matching, and the head tests cover a failed match not leaking context.
- **Stale cache after `router.mount()` or direct `routes` mutation:** base never included mounts, and the head docs say not to mutate `routes`.
- **Cycle assertion rejecting a mutual include:** base produced nonsensical duplicate routes in that case, so there is no realistic legitimate use.
- **Empty path added after a no-prefix include:** the route is unreachable at both base and head, so there is no regression.