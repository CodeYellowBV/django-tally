import json
import logging

from collections.abc import MutableMapping


logger = logging.getLogger(__name__)
stdenv = {}


class Env(MutableMapping):
    """
    An environment in the language.
    """

    def __init__(self, env=None, base_env=stdenv):
        if env is None:
            env = {}
        self.__dict = env
        self.__base = base_env
        self.__base_filter = set()

    def __getitem__(self, key):
        try:
            return self.__dict[key]
        except KeyError:
            if key in self.__base_filter:
                raise
            return self.__base[key]

    def __setitem__(self, key, value):
        self.__dict[key] = value

    def __delitem__(self, key):
        if key in self.__dict:
            del self.__dict[key]
        if key in self.__base:
            self.__base_filter.add(key)

    def __iter__(self):
        yield from self.__dict
        yield from (
            key for key in self.__base
            if key not in self.__dict and key not in self.__base_filter
        )

    def __len__(self):
        return len(self.__dict) + sum(
            1 for key in self.__base
            if key not in self.__dict and key not in self.__base_filter
        )


class LangException(Exception):
    """
    An exception in the language.
    """

    def __init__(self, exc, trace=None):
        if trace is None:
            trace = []
        self.exc = exc
        self.trace = trace

    def __str__(self):
        return '{}: {}'.format(type(self.exc).__name__, self.exc)


class KW:
    """
    A keyword in the language.
    """

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return self.value

    def __eq__(self, other):
        return isinstance(other, KW) and self.value == other.value

    def __hash__(self):
        return hash((KW, self.value))


class Func:
    """
    A function in the language.
    """

    def __init__(self, spec, body, env, name='<anonymous>'):
        self.spec = spec
        self.body = body
        self.env = env
        self.name = name

        if name != '<anonymous>':
            self.env[name] = self

    def __call__(self, args, env):
        func_env = Env(base_env=self.env)
        args = [KW('quote'), [run(arg, env) for arg in args]]
        lang_def([self.spec, args], func_env)
        try:
            return run(self.body, func_env)
        except LangException as exc:
            exc.trace.insert(0, self.name)
            raise exc


def run(body, env=None, log=False):
    """
    Run a body of code.

    @param body: Any
        The body to run.
    @param env: Mapping
        The current environment.
    @return: Any
        The result of running the body.
    """
    if env is None:
        env = Env()
    try:
        if isinstance(body, KW):
            if body.value not in env:
                raise LangException(NameError(
                    'name {!r} is not defined'
                    .format(body.value)
                ))
            return env[body.value]
        elif isinstance(body, list):
            if not body:
                raise LangException(ValueError(
                    'can\'t execute empty s-expression'
                ))

            func = run(body[0], env)
            if isinstance(func, (list, dict, tuple)):
                params = [[KW('quote'), func], *body[1:]]
                func = lang_get
            elif not callable(func):
                raise LangException(ValueError(
                    'first argument of s-expression does not evaluate to '
                    'callable'
                ))
            else:
                params = body[1:]

            return func(params, env)
        else:
            return body
    except LangException as e:
        if log:
            logger.error(str(e))
        else:
            raise


# Below here only stdenv implementation
def register(name):
    def res(func):
        def wrapped_func(args, env):
            try:
                return func(args, env)
            except LangException as exc:
                exc.trace.insert(0, name)
                raise exc
            except Exception as exc:
                raise LangException(exc, trace=[name])
        stdenv[name] = wrapped_func
        return wrapped_func
    return res


@register('list')
def lang_list(args, env):
    return [run(arg, env) for arg in args]


@register('tuple')
def lang_tuple(args, env):
    return tuple(run(arg, env) for arg in args)


@register('set')
def lang_set(args, env):
    return {run(arg, env) for arg in args}


@register('dict')
def lang_dict(args, env):
    if len(args) % 2 != 0:
        raise TypeError(
            'expected an even amount of arguments, got {}'
            .format(len(args))
        )
    return {
        run(key, env): run(val, env)
        for key, val in zip(args[::2], args[1::2])
    }


@register('quote')
def lang_quote(args, env):
    if len(args) != 1:
        raise TypeError('expected 1 argument, got {}'.format(len(args)))
    if isinstance(args[0], list):
        if (
            len(args[0]) >= 1 and
            isinstance(args[0][0], KW) and
            args[0][0].value == 'unquote'
        ):
            assert len(args[0]) == 2, (
                'Exactly one value must follow after unquote'
            )
            return run(args[0][1], env)
        else:
            return [lang_quote([subarg], env) for subarg in args[0]]
    else:
        return args[0]


@register('eval')
def lang_unquote(args, env):
    if len(args) != 1:
        raise TypeError('expected 1 argument, got {}'.format(len(args)))
    return run(run(args[0], env), env)


@register('+')
def lang_add(args, env):
    res = 0
    for arg in args:
        res += run(arg, env)
    return res


@register('-')
def lang_sub(args, env):
    if not args:
        raise TypeError(
            'expected at least 1 argument, got {}'
            .format(len(args))
        )
    res = run(args[0], env)
    for arg in args[1:]:
        res -= run(arg, env)
    return res


@register('*')
def lang_mul(args, env):
    res = 1
    for arg in args:
        res *= run(arg, env)
    return res


@register('/')
def lang_div(args, env):
    if not args:
        raise TypeError(
            'expected at least 1 argument, got {}'
            .format(len(args))
        )
    res = run(args[0], env)
    for arg in args[1:]:
        res /= run(arg, env)
    return res


@register('=')
def lang_eq(args, env):
    if not args:
        raise TypeError(
            'expected at least 1 argument, got {}'
            .format(len(args))
        )
    lhs = run(args[0], env)
    for rhs in args[1:]:
        rhs = run(rhs, env)
        if lhs != rhs:
            return False
        lhs = rhs
    return True


@register('!=')
def lang_neq(args, env):
    if not args:
        raise TypeError(
            'expected at least 1 argument, got {}'
            .format(len(args))
        )
    lhs = run(args[0], env)
    for rhs in args[1:]:
        rhs = run(rhs, env)
        if lhs == rhs:
            return False
        lhs = rhs
    return True


@register('<')
def lang_lt(args, env):
    if not args:
        raise TypeError(
            'expected at least 1 argument, got {}'
            .format(len(args))
        )
    lhs = run(args[0], env)
    for rhs in args[1:]:
        rhs = run(rhs, env)
        if lhs >= rhs:
            return False
        lhs = rhs
    return True


@register('>')
def lang_gt(args, env):
    if not args:
        raise TypeError(
            'expected at least 1 argument, got {}'
            .format(len(args))
        )
    lhs = run(args[0], env)
    for rhs in args[1:]:
        rhs = run(rhs, env)
        if lhs <= rhs:
            return False
        lhs = rhs
    return True


@register('<=')
def lang_leq(args, env):
    if not args:
        raise TypeError(
            'expected at least 1 argument, got {}'
            .format(len(args))
        )
    lhs = run(args[0], env)
    for rhs in args[1:]:
        rhs = run(rhs, env)
        if lhs > rhs:
            return False
        lhs = rhs
    return True


@register('>=')
def lang_geq(args, env):
    if not args:
        raise TypeError(
            'expected at least 1 argument, got {}'
            .format(len(args))
        )
    lhs = run(args[0], env)
    for rhs in args[1:]:
        rhs = run(rhs, env)
        if lhs < rhs:
            return False
        lhs = rhs
    return True


@register('and')
def lang_and(args, env):
    return all(run(arg, env) for arg in args)


@register('or')
def lang_or(args, env):
    return any(run(arg, env) for arg in args)


@register('not')
def lang_not(args, env):
    return all(not run(arg, env) for arg in args)


@register('do')
def lang_do(args, env):
    res = None
    for arg in args:
        res = run(arg, env)
    return res


@register('if')
def lang_if(args, env):
    if not 2 <= len(args) <= 3:
        raise TypeError('expected 2 or 3 arguments, got {}'.format(len(args)))
    if run(args[0], env):
        return run(args[1], env)
    else:
        return run(args[2], env) if len(args) == 3 else None


@register('def')
def lang_def(args, env):
    if len(args) != 2:
        raise TypeError('expected 2 arguments, got {}'.format(len(args)))

    spec, value = args
    value = run(value, env)

    if isinstance(spec, KW):
        if spec.value != '_':
            env[spec.value] = value
    elif (
        isinstance(spec, list) and
        len(spec) >= 1 and
        spec[0] == KW('list')
    ):
        assert isinstance(value, list), 'value must be a list'
        spec = spec[1:]
        assert len(value) == len(spec), 'value has incorrect length'
        for subargs in zip(spec, value):
            lang_def(list(subargs), env)
    elif (
        isinstance(spec, list) and
        len(spec) >= 1 and
        spec[0] == KW('tuple')
    ):
        assert isinstance(value, tuple), 'value must be a tuple'
        spec = spec[1:]
        assert len(value) == len(spec), 'value has incorrect length'
        for subargs in zip(spec, value):
            lang_def(list(subargs), env)
    elif (
        isinstance(spec, list) and
        len(spec) >= 1 and
        spec[0] == KW('dict')
    ):
        assert isinstance(value, dict), 'value must be a dict'
        spec = {
            run(key, env): subspec
            for key, subspec in zip(spec[1::2], spec[2::2])
        }
        assert len(value) == len(spec), 'value has incorrect length'
        for key, subspec in spec.items():
            assert key in value, 'value lacks key: ' + str(key)
            lang_def([subspec, value[key]], env)
    elif (
        isinstance(spec, list) and
        len(spec) >= 1 and
        spec[0] == KW('set')
    ):
        assert isinstance(value, set), 'value must be a set'
        spec = {run(key, env) for key in spec[1:]}
        assert len(value) == len(spec), 'value has incorrect length'
        for key in spec:
            assert key in value, 'value lacks value: ' + str(key)
    elif (
        isinstance(spec, list) and
        len(spec) >= 1 and
        spec[0] == KW('into_list')
    ):
        assert isinstance(value, list), 'value must be a list'
        for subspec in spec[1:]:
            if (
                isinstance(subspec, list) and
                len(subspec) >= 1 and
                subspec[0] == KW('list')
            ):
                assert len(value) >= len(subspec) - 1, (
                    'value has incorrect length'
                )
                subvalue = value[:len(subspec) - 1]
                value = value[len(subspec) - 1:]
            else:
                subvalue = value
                value = []
            lang_def([subspec, [KW('quote'), subvalue]], env)
    elif (
        isinstance(spec, list) and
        len(spec) >= 1 and
        spec[0] == KW('into_tuple')
    ):
        assert isinstance(value, tuple), 'value must be a tuple'
        for subspec in spec[1:]:
            if (
                isinstance(subspec, list) and
                len(subspec) >= 1 and
                subspec[0] == KW('tuple')
            ):
                assert len(value) >= len(subspec) - 1, (
                    'value has incorrect length'
                )
                subvalue = value[:len(subspec) - 1]
                value = value[len(subspec) - 1:]
            else:
                subvalue = value
                value = ()
            lang_def([subspec, [KW('quote'), subvalue]], env)
    elif (
        isinstance(spec, list) and
        len(spec) >= 1 and
        spec[0] == KW('into_dict')
    ):
        assert isinstance(value, dict), 'value must be a dict'
        value = dict(value)
        for subspec in spec[1:]:
            if (
                isinstance(subspec, list) and
                len(subspec) >= 1 and
                subspec[0] == KW('dict')
            ):
                for key, subsubspec in zip(subspec[1::2], subspec[2::2]):
                    key = run(key, env)
                    assert key in value, 'value lacks key: ' + str(key)
                    subvalue = value.pop(key)
                    lang_def([subsubspec, [KW('quote'), subvalue]], env)
            else:
                subvalue = value
                value = {}
                lang_def([subspec, [KW('quote'), subvalue]], env)
    elif (
        isinstance(spec, list) and
        len(spec) >= 1 and
        spec[0] == KW('into_set')
    ):
        assert isinstance(value, set), 'value must be a set'
        value = set(value)
        for subspec in spec[1:]:
            if (
                isinstance(subspec, list) and
                len(subspec) >= 1 and
                subspec[0] == KW('set')
            ):
                for key in subspec[1:]:
                    key = run(key, env)
                    assert key in value, 'value lacks value: ' + str(key)
                    value.remove(key)
            else:
                subvalue = value
                value = set()
                lang_def([subspec, [KW('quote'), subvalue]], env)
    else:
        spec = run(spec)
        assert value == spec, 'value has incorrect value'

    return value


@register('undef')
def lang_undef(args, env):
    if not all(isinstance(arg, KW) for arg in args):
        raise TypeError('all arguments must be a keyword')
    res = None
    for arg in args:
        res = env.pop(arg.value, None)
    return res


@register('def?')
def lang_def_check(args, env):
    if not all(isinstance(arg, KW) for arg in args):
        raise TypeError('all arguments must be a keyword')
    return all(arg.value in env for arg in args)


@register('fn')
def lang_fn(args, env):
    if len(args) < 2:
        raise TypeError(
            'expected at least 2 arguments, got {}'
            .format(len(args))
        )
    if not (
        isinstance(args[0], list) and
        len(args[0]) >= 1 and
        args[0][0] in {KW('list'), KW('list_into')}
    ):
        raise TypeError(
            'argument 0 must be a list that starts with list or list_into'
        )
    if len(args) > 2:
        body = [KW('do')] + list(args[1:])
    else:
        body = args[1]
    return Func(args[0], body, env)


@register('defn')
def lang_defn(args, env):
    if len(args) < 3:
        raise TypeError(
            'expected at least 3 arguments, got {}'
            .format(len(args))
        )
    if not isinstance(args[0], KW):
        raise TypeError('argument 0 must be a keyword')
    if not (
        isinstance(args[1], list) and
        len(args[1]) >= 1 and
        args[1][0] in {KW('list'), KW('list_into')}
    ):
        raise TypeError(
            'argument 1 must be a list that starts with list or list_into'
        )
    name = args[0].value
    if len(args) > 3:
        body = [KW('do')] + args[2:]
    else:
        body = args[2]
    func = Func(args[1], body, env, name=name)
    return func


@register('len')
def lang_len(args, env):
    return sum(len(run(arg, env)) for arg in args)


@register('in')
def lang_in(args, env):
    if not args:
        raise TypeError(
            'expected at least 1 argument, got {}'
            .format(len(args))
        )
    col = run(args[0], env)
    for arg in args[1:]:
        if run(arg, env) not in col:
            return False
    return True


@register('get')
def lang_get(args, env):
    if not 2 <= len(args) <= 3:
        raise TypeError('expected 2 or 3 arguments, got {}'.format(len(args)))
    col = run(args[0], env)
    key = run(args[1], env)

    if len(args) == 3 and (
        key not in col
        if isinstance(col, dict) else
        not 0 <= key < len(col)
    ):
        return run(args[2], env)
    return col[key]


@register('put')
def lang_put(args, env):
    if len(args) != 3:
        raise TypeError('expected 3 arguments, got {}'.format(len(args)))
    value = run(args[2], env)
    run(args[0], env)[run(args[1], env)] = value
    return value


@register('del')
def lang_del(args, env):
    if not args:
        raise TypeError(
            'expected at least one argument, got {}'
            .format(len(args))
        )
    col = run(args[0], env)
    res = None
    for arg in args[1:]:
        res = col.pop(run(arg, env))
    return res


@register('slice')
def lang_slice(args, env):
    if not 2 <= len(args) <= 4:
        raise TypeError('expected 2 to 4 arguments, got {}'.format(len(args)))
    col = run(args[0], env)
    indici = []
    for i, arg in enumerate(args[1:]):
        indici.append(run(arg, env))
        if not isinstance(indici[-1], int):
            raise TypeError('argument {} must be int'.format(1 + i))
    start = 0
    step = 1
    if len(indici) == 1:
        stop = indici[0]
    elif len(indici) == 2:
        start, stop = indici
    else:
        start, stop, step = indici
    return col[start:stop:step]


@register('str')
def lang_str(args, env):
    return ''.join(str(run(arg, env)) for arg in args)


@register('kw')
def lang_kw(args, env):
    return KW(lang_str(args, env))


@register('cat')
def lang_cat(args, env):
    res = []
    for arg in args:
        arg = run(arg, env)
        if isinstance(arg, dict):
            arg = arg.items()
        res.extend(arg)
    return res


@register('split')
def lang_split(args, env):
    if len(args) != 2:
        raise TypeError('expected 2 arguments, got {}'.format(len(args)))
    return run(args[0], env).split(run(args[1], env))


@register('null?')
def lang_null_check(args, env):
    return all(run(arg, env) is None for arg in args)


@register('int?')
def lang_int_check(args, env):
    return all(isinstance(run(arg, env), int) for arg in args)


@register('float?')
def lang_float_check(args, env):
    return all(isinstance(run(arg, env), float) for arg in args)


@register('bool?')
def lang_bool_check(args, env):
    return all(isinstance(run(arg, env), bool) for arg in args)


@register('str?')
def lang_str_check(args, env):
    return all(isinstance(run(arg, env), str) for arg in args)


@register('list?')
def lang_list_check(args, env):
    return all(isinstance(run(arg, env), list) for arg in args)


@register('dict?')
def lang_dict_check(args, env):
    return all(isinstance(run(arg, env), dict) for arg in args)


@register('tuple?')
def lang_tuple_check(args, env):
    return all(isinstance(run(arg, env), tuple) for arg in args)


@register('set?')
def lang_set_check(args, env):
    return all(isinstance(run(arg, env), set) for arg in args)


@register('kw?')
def lang_kw_check(args, env):
    return all(isinstance(run(arg, env), KW) for arg in args)


@register('func?')
def lang_func_check(args, env):
    return all(isinstance(run(arg, env), Func) for arg in args)


@register('not_null?')
def lang_not_null_check(args, env):
    return not lang_null_check(args, env)


@register('not_int?')
def lang_not_int_check(args, env):
    return not lang_int_check(args, env)


@register('not_float?')
def lang_not_float_check(args, env):
    return not lang_float_check(args, env)


@register('not_bool?')
def lang_not_bool_check(args, env):
    return not lang_bool_check(args, env)


@register('not_str?')
def lang_not_str_check(args, env):
    return not lang_str_check(args, env)


@register('not_list?')
def lang_not_list_check(args, env):
    return not lang_list_check(args, env)


@register('not_dict?')
def lang_not_dict_check(args, env):
    return not lang_dict_check(args, env)


@register('not_tuple?')
def lang_not_tuple_check(args, env):
    return not lang_tuple_check(args, env)


@register('not_set?')
def lang_not_set_check(args, env):
    return not lang_set_check(args, env)


@register('not_kw?')
def lang_not_kw_check(args, env):
    return not lang_kw_check(args, env)


@register('not_func?')
def lang_not_func_check(args, env):
    return not lang_func_check(args, env)


@register('->')
def lang_thread(args, env):
    if not args:
        raise TypeError(
            'expected at least 1 argument, got {}'
            .format(len(args))
        )
    if not all(isinstance(arg, list) for arg in args[1:]):
        raise TypeError('every argument after the first must be a list')
    body = args[0]
    for arg in args[1:]:
        body = [arg[0], body, *arg[1:]]
    return run(body, env)


@register('get_tally')
def lang_get_tally(args, env):
    if len(args) != 1:
        raise TypeError('expected 1 argument, got {}'.format(len(args)))
    if not isinstance(args[0], KW):
        raise TypeError('argument 0 must be KW')

    from ...data.models import Data
    return json.loads(Data.objects.get(name=args[0]).value)


@register('for')
def lang_for(args, env):
    if len(args) < 2:
        raise TypeError(
            'expected at least 2 argument, got {}'
            .format(len(args))
        )
    spec, col, *body = args
    if len(body) == 1:
        body = body[0]
    else:
        body = [KW('do'), *body]

    col = run(col, env)
    if isinstance(col, dict):
        col = col.items()

    res = None
    for item in col:
        lang_def([spec, [KW('quote'), item]], env)
        res = run(body, env)
    return res


def _lang_into(args, env):
    for arg in args:
        arg = run(arg, env)
        if isinstance(arg, dict):
            arg = arg.items()
        yield from arg


@register('into_list')
def lang_into_list(args, env):
    return list(_lang_into(args, env))


@register('into_tuple')
def lang_into_tuple(args, env):
    return tuple(_lang_into(args, env))


@register('into_dict')
def lang_into_dict(args, env):
    return dict(_lang_into(args, env))


@register('into_set')
def lang_into_set(args, env):
    return set(_lang_into(args, env))
