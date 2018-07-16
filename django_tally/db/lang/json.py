import json

from .lang import KW


def encode(data):
    """
    Encode lang expressions to be json compatible.

    @param data: Any
        The data to encode.
    @return: Any
        The data after encoding.
    """
    if isinstance(data, str):
        return 's:' + data
    elif isinstance(data, KW):
        return 'k:' + data.value
    elif isinstance(data, list):
        return [encode(item) for item in data]
    else:
        return data


def decode(data):
    """
    Decode lang expressions that are encoded to be json compatible.

    @param data: Any
        The data to decode.
    @return: Any
        The data after decoding.
    """
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
    """
    Encode lang expressions as json.

    @param obj: Any
        The expression to encode.
    @param args: List[Any]
        Additional arguments to pass on to json.dumps.
    @param kwargs: Mapping[str, Any]
        Additional keyword arguments to pass on to json.dumps.
    @return: str
        The expression encoded as json.
    """
    return json.dumps(encode(obj), *args, **kwargs)


def loads(*args, **kwargs):
    """
    Decode json into lang expressions.

    @param args: List[Any]
        Arguments to pass on to json.loads.
    @param kwargs: Mapping[str, Any]
        Keyword arguments to pass on to json.loads.
    @return: Any
        The expression decoded from json.
    """
    return decode(json.loads(*args, **kwargs))
