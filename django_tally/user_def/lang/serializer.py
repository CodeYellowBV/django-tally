from .lang import KW


COLLECTIONS = {
    KW('list'): ('[', ']'),
    KW('tuple'): ('{', '}'),
    KW('dict'): ('#{', '}'),
    KW('set'): ('#[', ']'),
}


def serialize(body, many=False):
    if many:
        return '\n'.join(map(serialize, body))
    elif body is None:
        return 'null'
    elif body is True:
        return 'true'
    elif body is False:
        return 'false'
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
        elif len(body) >= 1 and body[0] in COLLECTIONS:
            sym_open, sym_close = COLLECTIONS[body[0]]
            return sym_open + ' '.join(map(serialize, body[1:])) + sym_close
        else:
            return '({})'.format(' '.join(map(serialize, body)))
