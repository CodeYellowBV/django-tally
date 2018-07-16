import json

from .lang import KW


def encode(data):
    if isinstance(data, str):
        return 's:' + data
    elif isinstance(data, KW):
        return 'k:' + data.value
    elif isinstance(data, list):
        return [encode(item) for item in data]
    else:
        return data


def decode(data):
    if isinstance(data, str):
        if data.startswith('s:'):
            return data[2:]
        elif data.startswith('k:'):
            return KW(data[2:])
        else:
            raise ValueError('str instance without prefix')
    elif isinstance(data, list):
        return [decode(item) for item in data]
    else:
        return data


def dumps(obj, *args, **kwargs):
    return json.dumps(encode(obj), *args, **kwargs)


def loads(*args, **kwargs):
    return decode(json.loads(*args, **kwargs))
