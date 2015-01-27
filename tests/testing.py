# coding: utf-8

"""
Helper module by James Broadhead:
https://github.com/jamesbroadhead/bttrtwisted/blob/master/bttrtwisted/testing.py
"""
from mock import MagicMock

from twisted.internet import defer
from twisted.python import failure

_sentinel = object()


def gen_nondeferred_mock(return_value=_sentinel, func_dict=None, spec=None,
                         name='NDMock', side_effect=_sentinel):
    """
    Get a mock which cannot be mistaken for a Deferred

    @param return_value: A return value, passed directly to the Mock
                         constructor if set
    @param func_dict:    A dict of function-name : return_value to attach
                         to the mock
    """
    kwargs = {'name': name}
    if not return_value == _sentinel:
        kwargs['return_value'] = return_value
    if not side_effect == _sentinel:
        kwargs['side_effect'] = side_effect
    if spec is not None:
        kwargs['spec'] = spec

    m = MagicMock(**kwargs)

    # pylint: disable=unused-argument
    def notimpl(*args, **kwargs):
        raise NotImplementedError('You treated a Mock like a Deferred!')
    m.addCallback = notimpl
    m.addErrback = notimpl
    m.addBoth = notimpl
    m.addCallbacks = notimpl

    if func_dict is not None:
        for fn, res in func_dict.items():
            setattr(m, fn, gen_nondeferred_mock(return_value=res))

    return m


def dmockfunc(retval):
    """
    As dmockfunc, but uses side_effect to return a unique deferred on each
    call, so may be called multiple times
    """
    def se(*args, **kwargs):
        return defer.succeed(retval)

    return gen_nondeferred_mock(side_effect=se)


def fmockfunc(retval):
    """ Equivalent to dmockfunc, but for failures

    Remember: if you're playing with logged Exceptions, call flush_log to
    stop trial ERRORing
    """
    return dmockfunc(failure.Failure(retval))
