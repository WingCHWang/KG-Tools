#!/usr/bin/env python
# -*- coding: utf-8 -*-

import multiprocessing
from multiprocessing import Pool
import random
import time
from functools import reduce
import numbers

WORKERS = multiprocessing.cpu_count() - 1
del multiprocessing

def reduce_sets(sets):
    return reduce(lambda x, y: x | y, sets)


def reduce_lists(lists):
    return reduce(lambda x, y: x + y, lists)


def reduce_seqs(seqs):
    if seqs[0] is None:
        return None
    dtype = type(seqs[0])
    assert all([isinstance(ele, dtype) for ele in seqs]), "All element type must be same"
    if dtype == set:
        return reduce_sets(seqs)
    elif dtype == list:
        return reduce_lists(seqs)
    elif dtype == tuple:
        return tuple(reduce_seqs(d) for d in zip(*seqs))
    elif isinstance(seqs[0], numbers.Number):
        return reduce(lambda x, y: x + y, seqs)
    else:
        raise NotImplementedError


def parallel(fn, data, *args, shuffle=True, in_place=False, workers=WORKERS):
    print("Start %d workers for '%s'... (%s)" % (workers, fn.__qualname__, time.asctime(time.localtime(time.time()))))
    if shuffle:
        random.shuffle(data)

    total_size = len(data)
    batch_size = total_size // workers
    proc = []
    pool = Pool(processes=workers)
    for beg, end in zip(range(0, total_size, batch_size), range(batch_size, total_size + batch_size, batch_size)):
        batch = data[beg:end]
        p = pool.apply_async(fn, args=(batch, *args))
        proc.append(p)

    pool.close()
    pool.join()

    if not in_place:
        result = [p.get() for p in proc]
        result = reduce_seqs(result)
        if result is not None:
            return result
    print("Finish %d workers for '%s'... (%s)" % (workers, fn.__qualname__, time.asctime(time.localtime(time.time()))))


# test
if __name__ == "__main__":
    s = parallel(sum, list(range(100)), shuffle=False)
    print(s)
