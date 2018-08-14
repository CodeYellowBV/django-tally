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
        elif token.endswith('_OPEN'):
            tail = parse_tokens(tokens, outer=False, close=CLOSER[token])
            if token in INIT:
                yield [INIT[token], *tail]
            else:
                yield list(tail)
        elif token.endswith('_CLOSE'):
            if close == token:
                return
            else:
                raise ValueError('Unexpected ' + CLOSE_REP[token])
        elif token == 'QUOTE':
            yield [KW('quote'), next(parse_tokens(tokens, outer=False))]
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


def parse(body):
    return parse_tokens(tokenize(body))
