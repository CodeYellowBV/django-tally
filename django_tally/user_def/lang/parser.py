import re

from .lang import KW

OPERATORS = [
    '->', '*', '/', '+', '-', '=', '!=', '<=', '>=', '<', '>',
]
TOKENS = [
    ('FLOAT', r'[+-]?\d+\.\d+'),
    ('INT', r'[+-]?\d+'),
    ('KW', (
        r'|'.join(map(re.escape, OPERATORS)) +
        r'|[A-Za-z_][A-Za-z_-]*[?!]?'
    )),
    ('STRING', r'"([^\\"]|\\.)*"'),

    ('SEXPR_OPEN', r'\('),
    ('SEXPR_CLOSE', r'\)'),
    ('QUOTE', r'\''),

    ('WHITESPACE', r'\s+'),
    ('COMMENT', r';[^\n]*\n'),
]
IGNORE = {'WHITESPACE', 'COMMENT'}
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


def parse_tokens(tokens, outer=True, sexpr=False):
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
            yield list(parse_tokens(tokens, outer=False, sexpr=True))
        elif token == 'SEXPR_CLOSE':
            if sexpr:
                return
            else:
                raise ValueError('Unexpected )')
        elif token == 'QUOTE':
            yield [
                KW('quote'),
                next(parse_tokens(tokens, outer=False, sexpr=False)),
            ]
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
