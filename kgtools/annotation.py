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


def Parallel(workers=WORKERS, batch_size=1000, shuffle=True, after_hook=None):
    def outer(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            print(f"@Parallel[workers={workers}, batch_size={batch_size}]: parallel for {fn.__qualname__}.")

            obj, data, _args = tuple(), tuple(), tuple()
            if hasattr(args[0].__class__, fn.__name__):
                obj, data, *_args = args
                obj = (obj, )
            else:
                data, *_args = args

            if type(data) != list:
                data = list(data)

            # assert type(data) == list, "Type of data must be list"

            if shuffle:
                print(f"@Parallel[workers={workers}, batch_size={batch_size}]: shuffle data for {fn.__qualname__}.")
                random.shuffle(data)

            pool = Pool(workers)
            pool.terminate()
            pool.restart()

            total_size = len(data)

            proc = []
            for beg, end in zip(range(0, total_size, batch_size), range(batch_size, total_size + batch_size, batch_size)):
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


if __name__ == "__main__":
    # import re

    # class Decamelizer:
    #     def __init__(self):
    #         pass

    #     @Cache
    #     def foo(self, camel_case):
    #         decamelized = re.sub(r'([A-Za-z])(2|4)([A-CE-Za-ce-z])', r'\1 \2 \3', camel_case).strip()
    #         decamelized = re.sub(r'_', " ", decamelized)
    #         decamelized = re.sub(r'([A-Z]+)([A-Z][a-z0-9]+)', r'\1 \2', decamelized)
    #         decamelized = re.sub(r'([0-9]?[A-Z]+)', r' \1', decamelized)
    #         decamelized = re.sub(r'\s+', " ", decamelized).strip()
    #         return decamelized

    #     def bar(self, camel_case):
    #         decamelized = re.sub(r'([A-Za-z])(2|4)([A-CE-Za-ce-z])', r'\1 \2 \3', camel_case).strip()
    #         decamelized = re.sub(r'_', " ", decamelized)
    #         decamelized = re.sub(r'([A-Z]+)([A-Z][a-z0-9]+)', r'\1 \2', decamelized)
    #         decamelized = re.sub(r'([0-9]?[A-Z]+)', r' \1', decamelized)
    #         decamelized = re.sub(r'\s+', " ", decamelized).strip()
    #         return decamelized

    #     def __call__(self, camel_case):
    #         return self.foo(camel_case)

    # decamelizer = Decamelizer()
    # import time
    # start = time.time()
    # for _ in range(10000):
    #     decamelizer("StringBuilder")
    # end = time.time()
    # print(end - start)

    # start = time.time()
    # for _ in range(10000):
    #     decamelizer.bar("StringBuilder")
    # end = time.time()
    # print(end - start)
    # class Foo:
    #     def __init__(self):
    #         pass

    #     @Parallel(clazz="Foo")
    #     def split(self, data):
    #         return [s.split() for s in data]

    # @Parallel(clazz=None)
    # def foo(data):
    #     return [s.split() for s in data]

    # rs = foo(["a b c"] * 100)
    # print(rs)

    @Singleton
    class Foo:
        def __init__(self, a=1):
            self.a = a
            self.list = []

    foo1 = Foo()
    foo1.a = 2
    foo1.list.append(1)
    foo2 = Foo()
    print(foo1 == foo2)
    print(foo2.a)
    print(foo2.list)
