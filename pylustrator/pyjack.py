"""\
pyjack
******

pyjack is debug/test/monkey-patching toolset that allows you to reversibly
replace all references to a function /object in memory with a
proxy function/object.

:copyright: Copyright 2009-2012 by Andrew Carter <andrewjcarter@gmail.com>
:license: MIT (http://www.opensource.org/licenses/mit-license.php)

NOTE: adapted for pylustrator to be Python3 compatible

"""
import sys as _sys
import gc as _gc
import types as _types
import inspect as _inspect

_WRAPPER_TYPES = (type(object.__init__), type(object().__init__),)

# deactivated closure support as this code does not work for python3
"""
def proxy0(data):
    def proxy1(): return data

    return proxy1


_CELLTYPE = int  # type(proxy0(None).func_closure[0])
"""

class PyjackException(Exception): pass


def connect(fn, proxyfn):
    """\
    :summary: Connects a filter/callback function to a function/method.

    :param fn: The function which to pyjack.
    :type fn:  :class:`types.FunctionType`, :class:`types.MethodType`,
               :class:`types.BuiltinFunctionType`, :class:`BuiltinMethodType`
               or any callable that implements :func:`__call__`

    :param proxyfn: Any callable.  It will be passed the original :attr:`fn`
                    and then any args, kwargs that were passed to the
                    original :attr:`fn`.
    :type proxyfn:  callable.

    :returns: The new pyjacked function.  Note, this function object
              has a :func:`restore` that can be called to remove the
              pyjack filters/callbacks.

    :raises: :class:`PyjackException`
    """
    fn_type = type(fn)
    if issubclass(fn_type, _types.FunctionType):
        return _PyjackFuncCode(fn, proxyfn)._fn
    elif issubclass(fn_type, _types.MethodType):
        return _PyjackFuncCode(fn.im_func, proxyfn)._fn
    elif issubclass(fn_type, (_types.BuiltinFunctionType,
                              _types.BuiltinMethodType,
                              type)):
        return _PyjackFuncBuiltin(fn, proxyfn)
    elif _sys.version_info < (2, 5) and issubclass(fn_type, type(file)):
        # in python 2.4, open is of type file, not :class:`types.FunctionType`
        return _PyjackFuncBuiltin(fn, proxyfn)
    elif issubclass(fn_type, _WRAPPER_TYPES):
        raise PyjackException("Wrappers not supported. Make a concrete fn.")
    elif isinstance(getattr(fn, '__call__', None), _types.MethodType):
        _PyjackFuncCode(fn.__call__.im_func, proxyfn)

        def restore():
            fn.__call__.im_func.restore()
            delattr(fn, 'restore')

        fn.restore = restore
        return fn
    else:
        bundle = (fn, fn_type,)
        raise PyjackException("fn %r of type '%r' not supported" % bundle)


def restore(fn):
    """\
    :summary:  Fully restores function back to original state.

    :param fn: The pyjacked function returned by :func:`connect`.

    .. note::

       Any pyjacked function has a :func:`restore` method, too.  So you can
       call that instead of this procedural function -- it's up to you.

    """
    fn.restore()


# SOMETHING BROKEN IN TYPES MODULE


def replace_all_refs(org_obj, new_obj):
    """
    :summary: Uses the :mod:`gc` module to replace all references to obj
              :attr:`org_obj` with :attr:`new_obj` (it tries it's best,
              anyway).

    :param org_obj: The obj you want to replace.

    :param new_obj: The new_obj you want in place of the old obj.

    :returns: The org_obj

    Use looks like:

    >>> import pyjack
    >>> x = ('org', 1, 2, 3)
    >>> y = x
    >>> z = ('new', -1, -2, -3)
    >>> org_x = pyjack.replace_all_refs(x, z)
    >>> print x
    ('new', -1, -2, -3)
    >>> print y
    ('new', -1, -2, -3)
    >>> print org_x
    ('org', 1, 2, 3)

    To reverse the process, do something like this:

    >>> z = pyjack.replace_all_refs(z, org_x)
    >>> del org_x
    >>> print x
    ('org', 1, 2, 3)
    >>> print y
    ('org', 1, 2, 3)
    >>> print z
    ('new', -1, -2, -3)

    .. note:
        The obj returned is, by the way, the last copy of :attr:`org_obj` in
        memory; if you don't save a copy, there is no way to put state of the
        system back to original state.

    .. warning::

       This function does not work reliably on strings, due to how the
       Python runtime interns strings.

    """

    _gc.collect()

    hit = False
    for referrer in _gc.get_referrers(org_obj):

        # FRAMES -- PASS THEM UP
        if isinstance(referrer, _types.FrameType):
            continue

        # DICTS
        if isinstance(referrer, dict):

            cls = None

            # THIS CODE HERE IS TO DEAL WITH DICTPROXY TYPES
            if '__dict__' in referrer and '__weakref__' in referrer:
                for cls in _gc.get_referrers(referrer):
                    if _inspect.isclass(cls) and cls.__dict__ == referrer:
                        break

            for key, value in referrer.items():
                # REMEMBER TO REPLACE VALUES ...
                if value is org_obj:
                    hit = True
                    value = new_obj
                    referrer[key] = value
                    if cls:  # AGAIN, CLEANUP DICTPROXY PROBLEM
                        setattr(cls, key, new_obj)
                # AND KEYS.
                if key is org_obj:
                    hit = True
                    del referrer[key]
                    referrer[new_obj] = value

        # LISTS
        elif isinstance(referrer, list):
            for i, value in enumerate(referrer):
                if value is org_obj:
                    hit = True
                    referrer[i] = new_obj

        # SETS
        elif isinstance(referrer, set):
            referrer.remove(org_obj)
            referrer.add(new_obj)
            hit = True

        # TUPLE, FROZENSET
        elif isinstance(referrer, (tuple, frozenset,)):
            new_tuple = []
            for obj in referrer:
                if obj is org_obj:
                    new_tuple.append(new_obj)
                else:
                    new_tuple.append(obj)
            replace_all_refs(referrer, type(referrer)(new_tuple))

        # CELLTYPE (deactivated as it makes problems im Python3)
        #elif isinstance(referrer, _CELLTYPE):
        #    def proxy0(data):
        #        def proxy1(): return data

        #        return proxy1
        #
        #    proxy = proxy0(new_obj)
        #    newcell = proxy.func_closure[0]
        #    replace_all_refs(referrer, newcell)

        # FUNCTIONS
        elif isinstance(referrer, _types.FunctionType):
            localsmap = {}
            for key in ['func_code', 'func_globals', 'func_name',
                        'func_defaults', 'func_closure']:
                orgattr = getattr(referrer, key)
                if orgattr is org_obj:
                    localsmap[key.split('func_')[-1]] = new_obj
                else:
                    localsmap[key.split('func_')[-1]] = orgattr
            localsmap['argdefs'] = localsmap['defaults']
            del localsmap['defaults']
            newfn = _types.FunctionType(**localsmap)
            replace_all_refs(referrer, newfn)

        # OTHER (IN DEBUG, SEE WHAT IS NOT SUPPORTED).
        else:
            # debug:
            import sys
            # print(type(referrer), file=sys.stderr)
            pass

    #if hit is False:
    #    raise AttributeError("Object '%r' not found" % org_obj)

    return org_obj


_func_code_map = {}


def _get_self():
    global _func_code_map

    frame = _inspect.currentframe()
    code = frame.f_back.f_code
    return _func_code_map[code]


class _PyjackFunc(object): pass


class _PyjackFuncCode(_PyjackFunc):

    def __init__(self, fn, proxyfn):
        global _func_code_map

        self._fn, self._proxyfn = fn, proxyfn

        def proxy(*args, **kwargs):
            import pyjack
            self = pyjack._get_self()
            return self._process_fn(args, kwargs)

        _func_code_map[proxy.func_code] = self
        self._org_func_code = fn.func_code
        self._proxy_func_code = proxy.func_code
        fn.func_code = proxy.func_code

        fn.restore = self.restore

    def _process_fn(self, args, kwargs):
        self._fn.func_code = self._org_func_code
        value = self._proxyfn(self._fn, *args, **kwargs)
        self._fn.func_code = self._proxy_func_code
        return value

    def restore(self):
        self._fn.func_code = self._org_func_code


class _PyjackFuncBuiltin(_PyjackFunc):

    def __init__(self, fn, proxyfn):
        self._fn = replace_all_refs(fn, self)
        self._proxyfn = proxyfn

    def __call__(self, *args, **kwargs):
        return self._proxyfn(self._fn, *args, **kwargs)

    def __getattr__(self, attr):
        try:
            return getattr(self._fn, attr)
        except AttributeError:
            bundle = (self._fn, attr,)
            raise AttributeError("function %r has no attr '%s'" % bundle)

    def restore(self):
        replace_all_refs(self, self._fn)


if __name__ == '__main__':
    import doctest

    doctest.testmod(optionflags=524)

