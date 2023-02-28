import json
import sys
import datetime
from dateutil import parser

class LoggerWriter:
    def __init__(self, level: str):
        self.level = level

    def write(self, message: str):
        self.level(message)

    def flush(self):
        self.level(sys.stderr)

def get_multi_level_value(d, *keys: any, **kwargs: any):
    default = get_value(kwargs, 'default')

    depth = len(keys)
    for i in range(depth):
        key = keys[i]
        d = get_value(d, key)
        if d is None and i < depth:
            return default
    return d

def get_value(d, key: any, default: any = None):
    try:
        return d[key]
    except:
        return default

def get_config(*keys: str, **kwargs: any):
    default = get_value(kwargs, 'default')

    with open('./config/config.json', 'r') as f:
        config = json.loads(f.read())
        return get_multi_level_value(config, *keys, **kwargs)

def purify_category_name(name: str):
    return name.lower().strip()

def parse_timestamp(timestamp: str):
    try:
        return parser.parse(timestamp)
    except ValueError:
        return None
