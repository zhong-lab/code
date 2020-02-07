from inspect import signature, Parameter
from functools import partial

def duplicate_rename(existing_names, name, suffix=' {}'):
    if name not in existing_names:
        return name
    try:
        lindex, rindex = suffix.index('{'), suffix.index('}')
    except ValueError:
        raise
    # we need to reverse index
    _rindex = - (len(suffix) - rindex - 1)
    if not _rindex:
        _rindex = None
    duplicate_value = 2
    for existing_name in existing_names:
        if existing_name.startswith(name):
            existing_suffix = existing_name[len(name):]
            try:
                value = int(existing_suffix.rstrip()[lindex:_rindex])
            except ValueError:
                continue
            duplicate_value = max(duplicate_value, value + 1)
    return name + suffix.format(duplicate_value)

def signature_dispatch(f, args=None, kwargs=None):
    args = list() if args is None else args
    kwargs = dict() if kwargs is None else kwargs
    sig = signature(f)
    parameters = sig.parameters
    supply_args = list()
    supply_kwargs = dict()
    for parameter_name, parameter in parameters.items():
        name = parameter.name
        default = parameter.default
        kind = parameter.kind
        print(parameter.kind, supply_args, supply_kwargs)

        if kind == Parameter.POSITIONAL_ONLY:
            if args:
                supply_args.append(args.pop(0))
            else:
                raise ValueError
        elif kind == Parameter.POSITIONAL_OR_KEYWORD:
            if name in kwargs:
                supply_kwargs[name] = kwargs.pop(name)
            elif args:
                supply_args.append(args.pop(0))
            elif default != Parameter.empty:
                supply_kwargs[name] = default
            else:
                raise ValueError
        elif kind == Parameter.VAR_POSITIONAL:
            supply_args.extend(args)
        elif kind == Parameter.KEYWORD_ONLY:
            if name in kwargs:
                supply_kwargs[name] = kwargs.pop(name)
            else:
                raise ValueError
        elif kind == Parameter.VAR_KEYWORD:
            supply_kwargs.update(kwargs)

    return partial(f, *supply_args, **supply_kwargs)

def test_signature_dispatch():
    def a():
        return

    def b(a, b):
        print(a, b)

    def c(a, b, *args):
        print(a, b, args)

    def d(a=None, b=None):
        print(a, b)

    try:
        signature_dispatch(a)()
        signature_dispatch(a, [1, 2, 3], {'x': 1, 'y': 2, 'z': 3})()
        # signature_dispatch(b, [1])()
        signature_dispatch(b, [1, 2, 3])()
        signature_dispatch(b, [1], {'b': 2})()
        signature_dispatch(c, [1], {'b': 2})()
        signature_dispatch(d)()
        signature_dispatch(d, kwargs={'a': 1})()
        signature_dispatch(d, kwargs={'a': 1, 'b': 2, 'c': 3})()
    except ValueError:
        raise
    return

def test_duplicate_rename():
    existing_names = ['PlotWidget', 'PlotWidget 2']
    new_name = duplicate_rename(existing_names, 'PlotWidget')
    print(new_name)

if __name__ == '__main__':
    # test_signature_dispatch()
    test_duplicate_rename()
