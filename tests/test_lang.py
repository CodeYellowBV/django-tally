from django.test import TestCase

from django_tally.data.models import Data
from django_tally.user_def.lang import run, KW, LangException, Env, Func
from django_tally.user_def.lang.json import encode, decode, dumps, loads


sample = [
    KW('do'),
    [
        KW('defn'), KW('fib'), [KW('list'), KW('n')],
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
    [KW('def'), KW('res'), [KW('fib'), 10]],
    [KW('str'), 'fib(10) = ', KW('res')],
    KW('res'),
]
encoded_sample = [
    'k:do',
    [
        'k:defn', 'k:fib', ['k:list', 'k:n'],
        [
            'k:if', ['k:in', ['k:quote', [0, 1]], 'k:n'],
            1,
            [
                'k:+',
                ['k:fib', ['k:-', 'k:n', 1]],
                ['k:fib', ['k:-', 'k:n', 2]],
            ],
        ],
    ],
    ['k:def', 'k:res', ['k:fib', 10]],
    ['k:str', 's:fib(10) = ', 'k:res'],
    'k:res',
]
# (defn fib [n] (if (in (list 0 1) n) 1 (+ (fib (- n 1)) (fib (- n 2)))))
json_sample = (
    '['
        '"k:do", '
        '['
            '"k:defn", "k:fib", ["k:list", "k:n"], '
            '['
                '"k:if", ["k:in", ["k:quote", [0, 1]], "k:n"], '
                '1, '
                '['
                    '"k:+", '
                    '["k:fib", ["k:-", "k:n", 1]], '
                    '["k:fib", ["k:-", "k:n", 2]]'
                ']'
            ']'
        '], '
        '["k:def", "k:res", ["k:fib", 10]], '
        '["k:str", "s:fib(10) = ", "k:res"], '
        '"k:res"'
    ']'
)  # noqa: E131


class RunCountedFunc(Func):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.count = 0

    def __call__(self, *args, **kwargs):
        self.count += 1
        return super().__call__(*args, **kwargs)


class TestLang(TestCase):

    def test_run(self):
        self.runExpr(sample, 89)

    def test_exception(self):
        with self.assertRaises(LangException) as cm:
            run([KW('/'), 1, 0])
        self.assertEqual(
            str(cm.exception),
            'ZeroDivisionError: division by zero',
        )

    def test_kw_repr(self):
        self.assertEqual(
            repr([KW('foo'), 'bar', 'baz']),
            '[foo, \'bar\', \'baz\']'
        )

    def test_kw_eq(self):
        self.assertEqual(KW('foo'), KW('foo'))
        self.assertNotEqual(KW('foo'), KW('bar'))
        self.assertNotEqual(KW('foo'), 'foo')

    def test_kw_hash(self):
        self.assertEqual(hash(KW('foo')), hash(KW('foo')))
        self.assertNotEqual(hash(KW('foo')), hash(KW('bar')))
        self.assertNotEqual(hash(KW('foo')), 'foo')

    def test_func_call_wrong_args(self):
        self.runExpr([KW('defn'), KW('id'), [KW('list'), KW('x')], 'x'])
        self.runExprFail([KW('id')], AssertionError)

    def test_func_call_contains_exception(self):
        self.runExpr([KW('defn'), KW('func'), [KW('list')], [KW('/'), 1, 0]])
        self.runExprFail([KW('func')], ZeroDivisionError, trace=['func', '/'])

    def test_undefined_name(self):
        self.runExprFail(KW('foo'), NameError, 'name \'foo\' is not defined')

    def test_execute_empty_sexpr(self):
        self.runExprFail([], ValueError, 'can\'t execute empty s-expression')

    def test_execute_non_callable(self):
        self.runExprFail(
            [1], ValueError,
            'first argument of s-expression does not evaluate to callable'
        )

    def test_lang_exception_in_base_func(self):
        self.runExprFail(
            [KW('+'), [KW('/'), 1, 0]],
            ZeroDivisionError, 'division by zero',
        )

    def test_list(self):
        self.runExpr([KW('list'), 1, 2, 3], [1, 2, 3])

    def test_tuple(self):
        self.runExpr([KW('tuple'), 1, 2, 3], (1, 2, 3))

    def test_set(self):
        self.runExpr([KW('set'), 1, 2, 3], {1, 2, 3})

    def test_dict(self):
        self.runExpr([KW('dict'), 1, 2, 3, 4], {1: 2, 3: 4})
        self.runExprFail([KW('dict'), 1, 2, 3], TypeError)

    def test_quote(self):
        self.runExpr([KW('quote'), [1, 2, 3]], [1, 2, 3])
        self.runExprFail([KW('quote')], TypeError)

        self.runExpr(
            [KW('quote'), [1, 2, [KW('unquote'), [KW('+'), 1, 2]]]],
            [1, 2, 3],
        )

    def test_eval(self):
        self.runExpr(
            [KW('eval'), [KW('list'), [KW('quote'), KW('+')], 1, 2]],
            3,
        )
        self.runExprFail([KW('eval')], TypeError)

    def test_add(self):
        self.runExpr([KW('+'), 1, 2], 3)
        self.runExpr([KW('+'), 1, 2, 3], 6)
        self.runExpr([KW('+')], 0)

    def test_sub(self):
        self.runExpr([KW('-'), 1, 2], -1)
        self.runExpr([KW('-'), 1, 2, 3], -4)
        self.runExprFail([KW('-')], TypeError)

    def test_mul(self):
        self.runExpr([KW('*'), 1, 2], 2)
        self.runExpr([KW('*'), 1, 2, 3], 6)
        self.runExpr([KW('*')], 1)

    def test_div(self):
        self.runExpr([KW('/'), 1, 2], 1 / 2)
        self.runExpr([KW('/'), 1, 2, 3], 1 / 6)
        self.runExprFail([KW('/')], TypeError)

    def test_eq(self):
        self.runExpr([KW('='), 1, 1], True)
        self.runExpr([KW('='), 1, 2], False)
        self.runExpr([KW('='), None, None], True)
        self.runExpr([KW('='), 1, 'foo'], False)
        self.runExprFail([KW('=')], TypeError)

        self.assertIdCallCount(0)
        self.runExpr([
            KW('='),
            [KW('id'), 0],
            [KW('id'), 1],
            [KW('id'), 2],
        ])
        self.assertIdCallCount(2)

    def test_neq(self):
        self.runExpr([KW('!='), 1, 1], False)
        self.runExpr([KW('!='), 1, 2], True)
        self.runExpr([KW('!='), None, None], False)
        self.runExpr([KW('!='), 1, 'foo'], True)
        self.runExprFail([KW('!=')], TypeError)

        self.assertIdCallCount(0)
        self.runExpr([
            KW('!='),
            [KW('id'), 0],
            [KW('id'), 0],
            [KW('id'), 0],
        ])
        self.assertIdCallCount(2)

    def test_lt(self):
        self.runExpr([KW('<'), 1, 2], True)
        self.runExpr([KW('<'), 2, 1], False)
        self.runExpr([KW('<'), 1, 1], False)

        self.runExpr([KW('<'), 1, 2, 1], False)
        self.runExpr([KW('<'), 1, 2, 3], True)

        self.assertIdCallCount(0)
        self.runExpr([
            KW('<'),
            [KW('id'), 0],
            [KW('id'), 0],
            [KW('id'), 0],
        ])
        self.assertIdCallCount(2)

        self.runExprFail([KW('<')], TypeError)

    def test_gt(self):
        self.runExpr([KW('>'), 1, 2], False)
        self.runExpr([KW('>'), 2, 1], True)
        self.runExpr([KW('>'), 1, 1], False)

        self.runExpr([KW('>'), 1, 2, 1], False)
        self.runExpr([KW('>'), 3, 2, 1], True)

        self.assertIdCallCount(0)
        self.runExpr([
            KW('>'),
            [KW('id'), 0],
            [KW('id'), 0],
            [KW('id'), 0],
        ])
        self.assertIdCallCount(2)

        self.runExprFail([KW('>')], TypeError)

    def test_leq(self):
        self.runExpr([KW('<='), 1, 2], True)
        self.runExpr([KW('<='), 2, 1], False)
        self.runExpr([KW('<='), 1, 1], True)

        self.runExpr([KW('<='), 1, 2, 1], False)
        self.runExpr([KW('<='), 1, 2, 3], True)

        self.assertIdCallCount(0)
        self.runExpr([
            KW('<='),
            [KW('id'), 2],
            [KW('id'), 1],
            [KW('id'), 0],
        ])
        self.assertIdCallCount(2)

        self.runExprFail([KW('<=')], TypeError)

    def test_geq(self):
        self.runExpr([KW('>='), 1, 2], False)
        self.runExpr([KW('>='), 2, 1], True)
        self.runExpr([KW('>='), 1, 1], True)

        self.runExpr([KW('>='), 1, 2, 1], False)
        self.runExpr([KW('>='), 3, 2, 1], True)

        self.assertIdCallCount(0)
        self.runExpr([
            KW('>='),
            [KW('id'), 0],
            [KW('id'), 1],
            [KW('id'), 2],
        ])
        self.assertIdCallCount(2)

        self.runExprFail([KW('>=')], TypeError)

    def test_and(self):
        self.runExpr([KW('and')], True)
        self.runExpr([KW('and'), True, True], True)
        self.runExpr([KW('and'), False, True], False)
        self.runExpr([KW('and'), False, False], False)
        self.runExpr([KW('and'), False, True, True, False], False)

        self.assertIdCallCount(0)
        self.runExpr([KW('and'), [KW('id'), False], [KW('id'), True]])
        self.assertIdCallCount(1)

    def test_or(self):
        self.runExpr([KW('or')], False)
        self.runExpr([KW('or'), True, True], True)
        self.runExpr([KW('or'), False, True], True)
        self.runExpr([KW('or'), False, False], False)
        self.runExpr([KW('or'), False, True, True, False], True)

        self.assertIdCallCount(0)
        self.runExpr([KW('or'), [KW('id'), True], [KW('id'), True]])
        self.assertIdCallCount(1)

    def test_not(self):
        self.runExpr([KW('not')], True)
        self.runExpr([KW('not'), True, True], False)
        self.runExpr([KW('not'), False, True], False)
        self.runExpr([KW('not'), False, False], True)
        self.runExpr([KW('not'), False, True, True, False], False)

        self.assertIdCallCount(0)
        self.runExpr([KW('not'), [KW('id'), True], [KW('id'), True]])
        self.assertIdCallCount(1)

    def test_do(self):
        self.runExpr([KW('do'), 1, 2], 2)

    def test_if(self):
        self.runExprFail([KW('if')], TypeError)
        self.runExpr([KW('if'), True, 'foo', 'bar'], 'foo')
        self.runExpr([KW('if'), False, 'foo', 'bar'], 'bar')

    def test_def(self):
        self.assertNotIn('foo', self.env)
        self.runExpr([KW('def'), KW('foo'), 1])
        self.assertEqual(self.env['foo'], 1)

        self.runExprFail([KW('def')], TypeError)
        self.runExprFail([KW('def'), 'foo', 1], AssertionError)

    def test_def_match_tuple(self):
        self.assertNotIn('foo', self.env)
        self.runExpr([KW('def'), [KW('tuple'), KW('foo')], [KW('tuple'), 1]])
        self.assertEqual(self.env['foo'], 1)

    def test_def_match_dict(self):
        self.assertNotIn('foo', self.env)
        self.runExpr([
            KW('def'),
            [KW('dict'), True, KW('foo')],
            [KW('dict'), True, 1],
        ])
        self.assertEqual(self.env['foo'], 1)

    def test_def_match_set(self):
        self.runExpr([KW('def'), [KW('set'), 1, 2, 3], [KW('set'), 1, 2, 3]])

    def test_def_match_into_list(self):
        self.runExpr([
            KW('def'),
            [
                KW('into_list'),
                [KW('list'), 1, 2, 3],
                KW('foo'),
            ],
            [KW('list'), 1, 2, 3, 4, 5],
        ])
        self.assertEqual(self.env['foo'], [4, 5])

    def test_def_match_into_tuple(self):
        self.runExpr([
            KW('def'),
            [
                KW('into_tuple'),
                [KW('tuple'), 1, 2, 3],
                KW('foo'),
            ],
            [KW('tuple'), 1, 2, 3, 4, 5],
        ])
        self.assertEqual(self.env['foo'], (4, 5))

    def test_def_match_into_dict(self):
        self.runExpr([
            KW('def'),
            [
                KW('into_dict'),
                [KW('dict'), "foo", KW('foo')],
                KW('other'),
            ],
            [KW('dict'), "foo", 1, "bar", 2, "baz", 3],
        ])
        self.assertEqual(self.env['foo'], 1)
        self.assertEqual(self.env['other'], {"bar": 2, "baz": 3})

    def test_def_match_into_set(self):
        self.runExpr([
            KW('def'),
            [
                KW('into_set'),
                [KW('set'), "foo"],
                KW('other'),
            ],
            [KW('set'), "foo", "bar", "baz"],
        ])
        self.assertEqual(self.env['other'], {"bar", "baz"})

    def test_undef(self):
        self.env['foo'] = 1
        self.runExpr([KW('undef'), KW('foo')])
        self.assertNotIn('foo', self.env)

        self.assertIn('list', self.env)
        self.runExpr([KW('undef'), KW('list')])
        self.assertNotIn('list', self.env)

        self.runExprFail([KW('undef'), 'foo'], TypeError)

    def test_def_check(self):
        self.assertNotIn('foo', self.env)
        self.runExpr([KW('def?'), KW('foo')], False)
        self.env['foo'] = 1
        self.runExpr([KW('def?'), KW('foo')], True)

        self.runExprFail([KW('def?'), 'foo'], TypeError)

    def test_fn(self):
        self.runExpr(
            [
                [
                    KW('fn'), [KW('list'), KW('x')],
                    [KW('*'), KW('x'), KW('x')],
                ],
                2,
            ],
            4,
        )
        self.runExpr(
            [
                [
                    KW('fn'), [KW('list'), KW('x')],
                    [KW('def'), KW('n'), KW('x')],
                    [KW('*'), KW('n'), KW('n')],
                ],
                2,
            ],
            4,
        )

        self.runExprFail([KW('fn')], TypeError)
        self.runExprFail([KW('fn'), 'foo', 'bar'], TypeError)

    def test_defn(self):
        self.runExpr([
            KW('defn'), KW('sqr'), [KW('list'), KW('x')],
            [KW('*'), KW('x'), KW('x')],
        ])
        self.runExpr([KW('sqr'), 3], 9)
        self.runExpr([
            KW('defn'), KW('sqr'), [KW('list'), KW('x')],
            [KW('def'), KW('n'), KW('x')],
            [KW('*'), KW('n'), KW('n')],
        ])
        self.runExpr([KW('sqr'), 3], 9)

        self.runExprFail([KW('defn')], TypeError)
        self.runExprFail(
            [KW('defn'), 'foo', [KW('list'), KW('x')], [KW('x')]],
            TypeError,
        )
        self.runExprFail(
            [KW('defn'), KW('foo'), [KW('x')], [KW('x')]],
            TypeError,
        )
        self.runExprFail([KW('defn'), KW('foo'), 'bar', 'baz'], TypeError)

    def test_len(self):
        self.runExpr(
            [KW('len'), [KW('list'), 1, 2, 3], [KW('list'), 1, 2, 3]],
            6,
        )

    def test_in(self):
        self.runExpr([KW('in'), [KW('set'), 1, 2, 3], 1], True)
        self.runExpr([KW('in'), [KW('set'), 1, 2, 3], 4], False)
        self.runExpr([KW('in'), [KW('set'), 1, 2, 3], 1, 2], True)
        self.runExpr([KW('in'), [KW('set'), 1, 2, 3], 1, 4], False)
        self.runExprFail([KW('in')], TypeError)

    def test_get(self):
        self.runExpr([KW('def'), KW('d'), [KW('dict'), 'foo', 1, 'bar', 2]])
        self.runExpr([KW('get'), KW('d'), 'foo'], 1)
        self.runExprFail([KW('get'), KW('d'), 'baz'], KeyError)
        self.runExpr([KW('get'), KW('d'), 'baz', 3], 3)
        self.runExprFail([KW('get')], TypeError)

    def test_put(self):
        self.runExpr([KW('def'), KW('d'), [KW('dict'), 'foo', 1, 'bar', 2]])
        self.runExpr([KW('put'), KW('d'), 'foo', 3])
        self.runExpr([KW('get'), KW('d'), 'foo'], 3)
        self.runExprFail([KW('put')], TypeError)

    def test_del(self):
        self.runExpr([KW('def'), KW('d'), [KW('dict'), 'foo', 1, 'bar', 2]])
        self.runExpr([KW('del'), KW('d'), 'foo'])
        self.runExprFail([KW('get'), KW('d'), 'foo'], KeyError)
        self.runExprFail([KW('del')], TypeError)

    def test_slice(self):
        self.runExpr([
            KW('def'), KW('l'),
            [KW('list'), 0, 1, 2, 3, 4, 5, 6, 7]
        ])
        self.runExpr([KW('slice'), KW('l'), 4], [0, 1, 2, 3])
        self.runExpr([KW('slice'), KW('l'), 2, 6], [2, 3, 4, 5])
        self.runExpr([KW('slice'), KW('l'), 0, 8, 2], [0, 2, 4, 6])
        self.runExprFail([KW('slice')], TypeError)
        self.runExprFail([KW('slice'), KW('l'), 'foo'], TypeError)

    def test_str(self):
        self.runExpr([KW('str'), 'foo', 'bar', 123], 'foobar123')

    def test_cat(self):
        self.runExpr([
            KW('cat'),
            [KW('list'), 'foo'],
            [KW('tuple'), 'bar'],
            [KW('dict'), 'foo', 'bar'],
        ], ['foo', 'bar', ('foo', 'bar')])

    def test_split(self):
        self.runExpr([KW('split'), 'foo,bar,baz', ','], ['foo', 'bar', 'baz'])
        self.runExprFail([KW('split')], TypeError)

    def test_call_dict(self):
        self.runExpr([[KW('dict'), 'foo', 1, 'bar', 2], 'foo'], 1)

    def test_typechecks(self):
        type_checks = {
            'null?': lambda x: x is None,
            'not_null?': lambda x: x is not None,
            'int?': lambda x: isinstance(x, int),
            'not_int?': lambda x: not isinstance(x, int),
            'float?': lambda x: isinstance(x, float),
            'not_float?': lambda x: not isinstance(x, float),
            'bool?': lambda x: isinstance(x, bool),
            'not_bool?': lambda x: not isinstance(x, bool),
            'str?': lambda x: isinstance(x, str),
            'not_str?': lambda x: not isinstance(x, str),
            'list?': lambda x: isinstance(x, list),
            'not_list?': lambda x: not isinstance(x, list),
            'dict?': lambda x: isinstance(x, dict),
            'not_dict?': lambda x: not isinstance(x, dict),
            'tuple?': lambda x: isinstance(x, tuple),
            'not_tuple?': lambda x: not isinstance(x, tuple),
            'set?': lambda x: isinstance(x, set),
            'not_set?': lambda x: not isinstance(x, set),
            'kw?': lambda x: isinstance(x, KW),
            'not_kw?': lambda x: not isinstance(x, KW),
            'func?': lambda x: isinstance(x, Func),
            'not_func?': lambda x: not isinstance(x, Func),
        }
        values = [
            None, KW('foo'), 'foo', 1, 1.5, {'foo': 1}, ['bar'],
            ('foo', 'bar'), {'foo', 'bar', 'baz'},
            Func([KW('foo')], KW('foo'), self.env),
        ]
        for name, type_check in type_checks.items():
            with self.subTest(name):
                for value in values:
                    self.runExpr(
                        [KW(name), [KW('quote'), value]],
                        type_check(value),
                    )

    def test_thread(self):
        self.runExpr([
            KW('->'), 10,
            [KW('-'), 2],
            [KW('*'), 3],
            [KW('/'), 4],
        ], 6)
        self.runExprFail([KW('->')], TypeError)
        self.runExprFail([KW('->'), 'foo', 'bar'], TypeError)

    def test_get_tally(self):
        Data(name='foo', value='5').save()
        self.runExpr([KW('get_tally'), KW('foo')], 5)
        self.runExprFail([KW('get_tally')], TypeError)
        self.runExprFail([KW('get_tally'), 'foo'], TypeError)

    def test_kw(self):
        self.runExpr([KW('kw'), 'foo'], KW('foo'))
        self.runExpr([KW('kw'), 'foo', 'bar'], KW('foobar'))

    def test_for(self):
        self.env['foo'] = 0
        self.runExpr([
            KW('for'),
            [KW('tuple'), KW('_'), KW('n')],
            [KW('dict'), 1, 1, 2, 2, 3, 3],
            [KW('def'), KW('foo'), [KW('+'), KW('foo'), KW('n')]],
            [KW('def'), KW('foo'), [KW('+'), KW('foo'), KW('n')]],
        ])
        self.assertEqual(self.env['foo'], 12)

        self.runExprFail([KW('for')], TypeError)

    def test_into_list(self):
        self.runExpr(
            [
                KW('into_list'),
                [KW('quote'), [1, 2, 3]],
                [KW('quote'), (4, 5, 6)],
                [KW('quote'), {'foo': 'bar'}],
                [KW('quote'), {'baz'}],
            ],
            [1, 2, 3, 4, 5, 6, ('foo', 'bar'), 'baz'],
        )

    def test_into_tuple(self):
        self.runExpr(
            [
                KW('into_tuple'),
                [KW('quote'), [1, 2, 3]],
                [KW('quote'), (4, 5, 6)],
                [KW('quote'), {'foo': 'bar'}],
                [KW('quote'), {'baz'}],
            ],
            (1, 2, 3, 4, 5, 6, ('foo', 'bar'), 'baz'),
        )

    def test_into_dict(self):
        self.runExpr(
            [
                KW('into_dict'),
                [KW('quote'), [(1, 2), (3, 4)]],
                [KW('quote'), ((5, 6),)],
                [KW('quote'), {'foo': 'bar'}],
            ],
            {1: 2, 3: 4, 5: 6, 'foo': 'bar'},
        )

    def test_into_set(self):
        self.runExpr(
            [
                KW('into_set'),
                [KW('quote'), [1, 2, 3]],
                [KW('quote'), (4, 5, 6)],
                [KW('quote'), {'foo': 'bar'}],
                [KW('quote'), {'baz'}],
            ],
            {1, 2, 3, 4, 5, 6, ('foo', 'bar'), 'baz'},
        )

    def test_run_log(self):
        # Without log
        with self.assertRaises(LangException):
            run([KW('/'), 1, 0])
        # With log
        run([KW('/'), 1, 0], log=True)

    # helper methods
    def setUp(self):
        self.env = Env()
        self.identity = RunCountedFunc(
            [KW('list'), KW('x')],
            KW('x'),
            self.env, 'id',
        )

    def reset(self):
        self.env = Env()

    def runExpr(self, expr, *result):
        res = run(expr, self.env)
        if result:
            self.assertEqual(res, result[0])

    def runExprFail(self, expr, exc, msg=None, trace=None):
        with self.assertRaises(LangException) as cm:
            run(expr, self.env)
        self.assertEqual(type(cm.exception.exc), exc)
        if msg is not None:
            self.assertEqual(str(cm.exception.exc), msg)
        if trace is not None:
            self.assertEqual(cm.exception.trace, trace)

    def assertIdCallCount(self, n):
        self.assertEqual(self.identity.count, n)


class TestEnv(TestCase):

    def setUp(self):
        self.env = Env(env={'foo': 1, 'bar': 1}, base_env={'bar': 2, 'baz': 2})

    def test_get(self):
        self.assertEqual(self.env['foo'], 1)

    def test_iter(self):
        self.assertEqual(set(self.env), {'foo', 'bar', 'baz'})

    def test_len(self):
        self.assertEqual(len(self.env), 3)


class TestLangJSON(TestCase):

    def test_encode(self):
        self.assertEqual(encode(sample), encoded_sample)

    def test_decode(self):
        self.assertEqual(decode(encoded_sample), sample)

    def test_dumps(self):
        self.assertEqual(dumps(sample), json_sample)

    def test_loads(self):
        self.assertEqual(loads(json_sample), sample)

    def test_decode_incorrect_str(self):
        with self.assertRaises(ValueError):
            decode('foo')
