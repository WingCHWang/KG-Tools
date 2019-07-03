#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import threading
import multiprocessing
import random
from functools import wraps
from pathos.multiprocessing import ProcessingPool as Pool

from kgtools.func import reduce_seqs

WORKERS = multiprocessing.cpu_count() - 1


def TimeLog(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        print("@TimeLog[%s]: %s starts." % (time.strftime("%X", time.localtime()), fn.__qualname__))
        start = time.time()
        rs = fn(*args, **kwargs)
        end = time.time()
        print("@TimeLog[%s]: %s finishes." % (time.strftime("%X", time.localtime()), fn.__qualname__))
        print("@TimeLog[%fs]: %s takes." % (end - start, fn.__qualname__))
        return rs
    return wrapper


class Lazy(object):
    def __init__(self, func):
        self.func = func
        print("@Lazy[%s]: lazy property is declared." % self.func.__qualname__)

    def __get__(self, instance, cls):
        val = self.func(instance)
        setattr(instance, self.func.__name__, val)
        return val


def ID(*prime_keys):
    def wrapper(clazz):
        clazz.__str__ = lambda obj: '<{}: {}>'.format(obj.__class__.__name__, " ".join([f"{key}={str(obj.__dict__[key])}" for key in prime_keys]))
        clazz.__repr__ = lambda obj: '<{}: {}>'.format(obj.__class__.__name__, " ".join([f"{k}={str(v)}" for k, v in obj.__dict__.items()]))
        clazz.__eq__ = lambda obj, other: hash(obj) == hash(other)
        clazz.__hash__ = lambda obj: hash(str(obj))
        return clazz
    return wrapper


def Singleton(clazz):
    def new(cls, *args, **kwargs):
        if not hasattr(cls, "__instance"):
            with threading.Lock():
                if not hasattr(cls, "__instance"):
                    print("@Singleton[%s]: initialize singleton object." % cls.__name__)
                    cls.__instance = object.__new__(cls)
                    cls.__instance.__init__(*args, **kwargs)
        # print("@Singleton[%s]: get singleton object." % cls.__name__)
        return cls.__instance

    if not hasattr(clazz, "__Singleton"):
        with threading.Lock():
            if not hasattr(clazz, "__Singleton"):
                clazz.__Singleton = True
                clazz.__new__ = new
    return clazz


def Cache(fn):
    cache = {}
    print("@Cache[%s]: add cache." % fn.__qualname__)

    @wraps(fn)
    def wrapper(*arg):
        if arg not in cache:
            result = fn(*arg)
            cache[arg] = result
        return cache[arg]
    return wrapper


def Parallel(workers=WORKERS, batch_size=None, shuffle=True, after_hook=None):
    def outer(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):

            obj, data, _args = tuple(), tuple(), tuple()
            if hasattr(args[0].__class__, fn.__name__):
                obj, data, *_args = args
                obj = (obj, )
            else:
                data, *_args = args

            if type(data) != list:
                data = list(data)

            total_size = len(data)
            _batch_size = total_size // workers + 1 if batch_size is None else batch_size
            # assert type(data) == list, "Type of data must be list"
            print(f"@Parallel[workers={workers}, data_size={total_size}, batch_size={_batch_size}]: parallel for {fn.__qualname__}.")
            
            if shuffle:
                print(f"@Parallel[workers={workers}, data_size={total_size}, batch_size={_batch_size}]: shuffle data for {fn.__qualname__}.")
                random.shuffle(data)

            pool = Pool(workers)
            pool.terminate()
            pool.restart()

            proc = []
            for beg, end in zip(range(0, total_size, _batch_size), range(_batch_size, total_size + _batch_size, _batch_size)):
                batch = data[beg:end]
                p = pool.apipe(fn, *obj, batch, *_args, **kwargs)
                proc.append(p)
            pool.close()
            pool.join()

            result = reduce_seqs([p.get() for p in proc])
            if after_hook is not None:
                result = after_hook(result)

            return result
        return wrapper
    return outer
