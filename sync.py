import asyncio

locks = {}
creation_lock = asyncio.Lock()

def get_lock(key):
    global locks
    if key in locks:
        return locks[key]
    with creation_lock:
        if key in locks:
            # Lock was created right after we checked the first time (should almost never happen)
            return locks[key]
        lock = asyncio.Lock()
        locks[key] = lock
        return lock
