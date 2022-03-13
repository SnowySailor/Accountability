import json

def get_multi_level_value(d: dict|list, *keys: any, **kwargs: any):
    default = get_value(kwargs, 'default')

    depth = len(keys)
    for i in range(depth):
        key = keys[i]
        d = get_value(d, key)
        if d is None and i < depth:
            return default
    return d

def get_value(d: dict|list, key: any, default: any = None):
    try:
        return d[key]
    except:
        return default

def get_config(*keys: str, **kwargs: any):
    default = get_value(kwargs, 'default')

    with open('config.json', 'r') as f:
        config = json.loads(f.read())
        return get_multi_level_value(config, *keys, **kwargs)
