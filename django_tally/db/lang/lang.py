from collections.abc import MutableMapping


stdenv = {}


class Env(MutableMapping):
    """
    An environment in the language.
    """

    def __init__(self, *args, base_env=stdenv, **kwargs):
        self.__dict = dict(*args, **kwargs)
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

    def __init__(self, params, body, env, name='<anonymous>'):
        self.params = params
        self.body = body
        self.env = env
        self.name = name

        if name != '<anonymous>':
            self.env[name] = self

    def __call__(self, args, env):
        if len(args) != len(self.params):
            raise LangException(TypeError(
                'expected {} argument{}, got {}'.format(
                    len(self.params),
                    '' if len(self.params) == 1 else 's',
                    len(args),
                )
            ), [self.name])
        func_env = Env(base_env=self.env)
        args = [run(arg, env) for arg in args]
        func_env.update(zip(self.params, args))
        try:
            return run(self.body, func_env)
        except LangException as exc:
            exc.trace.insert(0, self.name)
            raise exc


def run(body, env=None):
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
        if not callable(func):
            raise LangException(ValueError(
                'first argument of s-expression does not evaluate to callable'
            ))

        return func(body[1:], env)
    elif isinstance(body, dict):
        return {
            run(key, env): run(val, env)
            for key, val in body.items()
        }
    else:
        return body


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
    return args[0]


@register('unquote')
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
    if not args:
        raise TypeError(
            'expected at least 1 argument, got {}'
            .format(len(args))
        )
    for arg in args[:-1]:
        run(arg, env)
    return run(args[-1], env)


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
    if not isinstance(args[0], KW):
        raise TypeError('argument 0 must be a keyword')
    value = run(args[1], env)
    env[args[0].value] = value
    return value


@register('undef')
def lang_undef(args, env):
    if not all(isinstance(arg, KW) for arg in args):
        raise TypeError('all arguments must be a keyword')
    res = None
    for arg in args:
        res = env.pop(arg.value, None)
    return res


@register('fn')
def lang_fn(args, env):
    if len(args) < 2:
        raise TypeError(
            'expected at least 2 arguments, got {}'
            .format(len(args))
        )
    if not (
        isinstance(args[0], list) and
        all(isinstance(param, KW) for param in args[0])
    ):
        raise TypeError('argument 0 must be list of keywords')
    if len(args) > 2:
        body = [KW('do')] + list(args[1:])
    else:
        body = args[1]
    return Func([param.value for param in args[0]], body, env)


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
        all(isinstance(param, KW) for param in args[1])
    ):
        raise TypeError('argument 1 must be list of keywords')
    name = args[0].value
    if len(args) > 3:
        body = [KW('do')] + args[2:]
    else:
        body = args[2]
    func = Func([param.value for param in args[1]], body, env, name=name)
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


@register('cat')
def lang_cat(args, env):
    return sum((list(run(arg, env)) for arg in args), [])


@register('split')
def lang_split(args, env):
    if len(args) != 2:
        raise TypeError('expected 2 arguments, got {}'.format(len(args)))
    return run(args[0], env).split(run(args[1], env))
