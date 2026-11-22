import inspect, fastapi.routing as r
cls = getattr(r, "_IncludedRouter", None)
print("K3 _IncludedRouter present:", cls is not None)
if cls:
    src = inspect.getsource(cls.effective_candidates)
    print("K3 assigns empty shared list:", "self._effective_candidates = []" in src, "| lock used:", "lock" in src.lower())
