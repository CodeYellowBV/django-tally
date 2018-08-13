from unittest import TestCase

from django_tally.user_def.lang import parse, KW, serialize
from django_tally.user_def.lang.parser import parse_tokens


source = """
(do
  (defn fib (n)
    (if (in '(0 1) n)
      1
      (+ (fib (- n 1)) (fib (- n 2)))))
  (fib 10))
"""
body = [
    [
        KW('do'),
        [
            KW('defn'), KW('fib'), [KW('n')],
            [
                KW('if'), [KW('in'), [KW('quote'), [0, 1]], KW('n')],
                1,
                [
                    KW('+'),
                    [KW('fib'), [KW('-'), KW('n'), 1]],
                    [KW('fib'), [KW('-'), KW('n'), 2]],
                ],
            ],
        ],
        [KW('fib'), 10],
    ]
]


class ParserTest(TestCase):

    def test_parse(self):
        self.assertEqual(list(parse(source)), body)

    def test_serialize(self):
        self.assertEqual(list(parse(serialize(body, many=True))), body)

    def test_intermediate_error(self):
        with self.assertRaises(ValueError) as cm:
            list(parse('% foo'))
        self.assertEqual(str(cm.exception), 'Invalid body: %')

    def test_final_error(self):
        with self.assertRaises(ValueError) as cm:
            list(parse('foo %'))
        self.assertEqual(str(cm.exception), 'Invalid body: %')

    def test_unexpected_closing_paren(self):
        with self.assertRaises(ValueError) as cm:
            list(parse(')'))
        self.assertEqual(str(cm.exception), 'Unexpected )')

    def test_unexpected_eof(self):
        with self.assertRaises(ValueError) as cm:
            list(parse('('))
        self.assertEqual(str(cm.exception), 'Unexpected EOF')

    def test_invalid_tokens(self):
        with self.assertRaises(ValueError) as cm:
            list(parse_tokens([]))
        self.assertEqual(str(cm.exception), 'Expected more tokens')

    def test_parse_float(self):
        self.assertEqual(next(parse('0.123')), 0.123)

    def test_parse_string(self):
        self.assertEqual(next(parse('"foobar\\"\\n\\t\\r"')), 'foobar"\n\t\r')

    def test_serialize_string(self):
        self.assertEqual(serialize('foobar"\n\t\r'), '"foobar\\"\\n\\t\\r"')

    def test_parse_operators(self):
        self.assertEqual(
            list(parse('* / + - = != <= >= < > ->')),
            [
                KW('*'), KW('/'), KW('+'), KW('-'), KW('='), KW('!='),
                KW('<='), KW('>='), KW('<'), KW('>'), KW('->'),
            ],
        )
