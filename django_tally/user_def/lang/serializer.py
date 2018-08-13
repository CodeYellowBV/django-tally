from .lang import KW


def serialize(body, many=False):
    if many:
        return '\n'.join(map(serialize, body))
    elif isinstance(body, (int, float, KW)):
        return str(body)
    elif isinstance(body, str):
        return '"{}"'.format(
            body
            .replace('\\', '\\\\')
            .replace('"', '\\"')
            .replace('\n', '\\n')
            .replace('\t', '\\t')
            .replace('\r', '\\r')
        )
    elif isinstance(body, list):
        if len(body) == 2 and body[0] == KW('quote'):
            return '\'{}'.format(serialize(body[1]))
        else:
            return '({})'.format(' '.join(map(serialize, body)))
