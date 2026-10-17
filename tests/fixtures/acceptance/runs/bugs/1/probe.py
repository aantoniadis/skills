"""Probe for the fixture card: does an override's captured session survive overrides.clear()?"""
import gc
import weakref


class Session:
    pass


def main():
    session = Session()
    alive = weakref.ref(session)
    overrides = {"get_db": lambda captured=session: captured}
    cache = {id(overrides["get_db"]): overrides["get_db"]}  # the head's cache keeps the callable
    del session
    overrides.clear()
    gc.collect()
    print(f"head alive after overrides.clear(): {alive() is not None}")
    cache.clear()


if __name__ == "__main__":
    main()
