from .lang import KW


INTOS = {
    KW('into_list'): KW('list'),
    KW('into_tuple'): KW('tuple'),
    KW('into_dict'): KW('dict'),
    KW('into_set'): KW('set'),
}

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
            if len(body[1]) == 2 and body[1][0] == KW('unquote'):
                return '^{}'.format(serialize(body[1][1]))
            else:
                return '\'{}'.format(serialize(body[1]))
        elif len(body) >= 1 and body[0] in INTOS:
            items = []

            for child in body[1:]:
                if (
                    isinstance(child, list) and
                    len(child) >= 1 and
                    child[0] == INTOS[body[0]]
                ):
                    items.extend(map(serialize, child[1:]))
                else:
                    items.append('&{}'.format(serialize(child)))

            sym_open, sym_close = COLLECTIONS[INTOS[body[0]]]
            return sym_open + ' '.join(items) + sym_close
        else:
            if len(body) >= 1 and body[0] in COLLECTIONS:
                sym_open, sym_close = COLLECTIONS[body[0]]
                body = body[1:]
            else:
                sym_open = '('
                sym_close = ')'
            return sym_open + ' '.join(map(serialize, body)) + sym_close
