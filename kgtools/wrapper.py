#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time


def TimeLog(fn):
    def inner(*args, **kwargs):
        print("Start '%s'... (%s)" % (fn.__qualname__, time.asctime(time.localtime(time.time()))))
        rs = fn(*args, **kwargs)
        print("Finish '%s'... (%s)" % (fn.__qualname__, time.asctime(time.localtime(time.time()))))
        return rs
    return inner


class Lazy(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, cls):
        val = self.func(instance)
        setattr(instance, self.func.__name__, val)
        return val


def Singleton(cls):
    _instance = {}

    def _singleton(*args, **kargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kargs)
        return _instance[cls]

    return _singleton
