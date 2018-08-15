import re

from .lang import KW

OPERATORS = [
    '->', '*', '/', '+', '-', '=', '!=', '<=', '>=', '<', '>',
]
TOKENS = [
    ('NULL', r'null'),
    ('BOOL', r'true|false'),
    ('FLOAT', r'[+-]?\d+\.\d+'),
    ('INT', r'[+-]?\d+'),
    ('KW', (
        r'|'.join(map(re.escape, OPERATORS)) +
        r'|[A-Za-z_][A-Za-z0-9_]*[?!]?'
    )),
    ('STRING', r'"([^\\"]|\\.)*"'),

    ('SEXPR_OPEN', r'\('),
    ('SEXPR_CLOSE', r'\)'),
    ('LIST_OPEN', r'\['),
    ('LIST_CLOSE', r'\]'),
    ('TUPLE_OPEN', r'\{'),
    ('TUPLE_CLOSE', r'\}'),
    ('DICT_OPEN', r'\#\{'),
    ('SET_OPEN', r'\#\['),
    ('QUOTE', r'\''),
    ('PIN', r'\^'),
    ('SPREAD', r'\&'),

    ('WHITESPACE', r'\s+'),
    ('COMMENT', r';[^\n]*\n'),
]
IGNORE = {'WHITESPACE', 'COMMENT'}
CLOSER = {
    'SEXPR_OPEN': 'SEXPR_CLOSE',
    'LIST_OPEN': 'LIST_CLOSE',
    'TUPLE_OPEN': 'TUPLE_CLOSE',
    'DICT_OPEN': 'TUPLE_CLOSE',
    'SET_OPEN': 'LIST_CLOSE',
}
INIT = {
    'LIST_OPEN': KW('list'),
    'TUPLE_OPEN': KW('tuple'),
    'DICT_OPEN': KW('dict'),
    'SET_OPEN': KW('set'),
}
INTO = {
    'LIST_OPEN': KW('into_list'),
    'TUPLE_OPEN': KW('into_tuple'),
    'DICT_OPEN': KW('into_dict'),
    'SET_OPEN': KW('into_set'),
}
CLOSE_REP = {
    'SEXPR_CLOSE': ')',
    'LIST_CLOSE': ']',
    'TUPLE_CLOSE': '}',
}
TOKEN_RE = re.compile(r'|'.join(
    r'(?P<{}>{})'.format(token, regexp)
    for token, regexp in TOKENS
))


def tokenize(body):
    pos = 0
    for match in TOKEN_RE.finditer(body):
        if pos != match.start():
            yield ('ERROR', body[pos:match.start()])
        if match.lastgroup not in IGNORE:
            yield (match.lastgroup, match.group())
        pos = match.end()
    if pos != len(body):
        yield ('ERROR', body[pos:])
    yield ('EOF', '')


def parse_tokens(tokens, outer=True, close=None):
    tokens = iter(tokens)

    while True:
        try:
            token, body = next(tokens)
        except StopIteration:
            raise ValueError('Expected more tokens')

        if token == 'ERROR':
            raise ValueError('Invalid body: {}'.format(body))
        elif token == 'EOF':
            if outer:
                return
            else:
                raise ValueError('Unexpected EOF')
        elif token == 'SEXPR_OPEN':
            yield list(parse_tokens(tokens, outer=False, close='SEXPR_CLOSE'))
        elif token.endswith('_OPEN'):
            yield _parse_tokens_spread(tokens, token)
        elif token.endswith('_CLOSE'):
            if close == token:
                return
            else:
                raise ValueError('Unexpected ' + CLOSE_REP[token])
        elif token == 'QUOTE':
            yield [KW('quote'), next(parse_tokens(tokens, outer=False))]
        elif token == 'PIN':
            yield [
                KW('quote'),
                [KW('unquote'), next(parse_tokens(tokens, outer=False))],
            ]
        elif token == 'NULL':
            yield None
        elif token == 'BOOL':
            yield body == 'true'
        elif token == 'KW':
            yield KW(body)
        elif token == 'FLOAT':
            yield float(body)
        elif token == 'INT':
            yield int(body)
        elif token == 'STRING':
            chars = iter(body[1:-1])
            string = ''
            for char in chars:
                if char == '\\':
                    char = next(chars)
                    if char == 'n':
                        char = '\n'
                    if char == 't':
                        char = '\t'
                    if char == 'r':
                        char = '\r'
                string += char
            yield string
        else:
            raise ValueError('Unexpected token ' + token)


class PeekIter:

    def __init__(self, iterable):
        self._it = iter(iterable)
        self._peek = None
        self._peeked = False

    def __iter__(self):
        return self

    def __next__(self):
        if self._peeked:
            res = self._peek
            self._peek = None
            self._peeked = False
            return res
        return next(self._it)

    def peek(self):
        if not self._peeked:
            self._peek = next(self._it)
            self._peeked = True
        return self._peek

    def has_next(self):
        try:
            self.peek()
        except StopIteration:
            return False
        else:
            return True


def _parse_tokens_spread(tokens, kind):
    tokens = PeekIter(tokens)
    nodes = parse_tokens(tokens, outer=False, close=CLOSER[kind])

    res = [INTO[kind], [INIT[kind]]]
    while True:
        if tokens.has_next() and tokens.peek()[0] == 'SPREAD':
            next(tokens)
            if len(res[-1]) == 1:
                res.pop()
            try:
                res.append(next(nodes))
            except StopIteration:
                raise ValueError('Expected expression to spread')
            res.append([INIT[kind]])
            continue

        try:
            res[-1].append(next(nodes))
        except StopIteration:
            break

    if len(res) == 2:
        res = res[1]
    elif len(res[-1]) == 1:
        res.pop()
    return res


def parse(body):
    return parse_tokens(tokenize(body))
