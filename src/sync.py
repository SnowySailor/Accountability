import asyncio
from contextlib import contextmanager

locks = {}
creation_lock = asyncio.Lock()

@contextmanager
def get_lock(key):
    global locks
    if key in locks:
        yield locks[key]
        return

    with (yield from creation_lock):
        if key in locks:
            # Lock was created right after we checked the first time (should almost never happen)
            yield locks[key]
            return

        lock = asyncio.Lock()
        locks[key] = lock
        yield lock
