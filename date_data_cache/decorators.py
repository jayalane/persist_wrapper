""" Place to keep utility decorators """

import time
import traceback
import random
import persist_dict
import pprint
from functools import wraps

import sqlite3

def make_str_key(name, args, kw):
    args2 = [str(v) for v in args]
    return name + '-' + '-'.join(args2) + '-' + '-'.join(["%s-%s" % (k, v) for k, v in kw.items()])

def memo(check_func=None, mem_cache=True, cache_none=True):
    """This is fairly generic for non-class functions; check_func should return True to not cache; gets called with cached result & str_args"""
    def inner_memo(method):
        name = "memo_" + method.__name__
        stored_results = [persist_dict.PersistentDict('./' + name + '.sqlite', mem_cache=mem_cache)]

        @wraps(method)
        def memoized(*args, **kw):
            """The wrapper function for the decorated thing"""
            try:
            # try to get the cached result
                str_args = make_str_key(method.__name__, args, kw)
                res = stored_results[0][str_args]
                if not cache_none and not res:
                        raise KeyError('synthetic')
                # dangerous
                if check_func:
                    if check_func(res, str_args):
                        raise KeyError('synthetic')
                return res
            except (KeyError):
                # redo not found
                result = stored_results[0][str_args] = method(*args, **kw)
            except (sqlite3.OperationalError):
                # need to kill the persistent dictionary
                stored_results[0].close()  # kill the connection
                result = stored_results[0][str_args] = method(*args, **kw)
            return result
        memoized.persist_dict = stored_results  # allow caller to have access
        def add_res_as_key(res, *args, **kw):
            """To allow two different URLs be keys for same data"""
            str_args = make_str_key(method.__name__, args, kw)
            stored_results[0][str_args] = res
        memoized.also_use_key = add_res_as_key
        return memoized
    return inner_memo


def memo_self_with_dates(mem_cache=True):
    """This is not generic - it assumes a class with a month and day members"""
    stored_results = persist_dict.PersistentDict('./memo_special.sqlite')
    def inner_memo(method):
        @wraps(method)
        def memoized(*args):
            args2 = [str(v) for v in args[1:]]  # meant for objects but want to skip self
            str_args = method.__name__ + '-' + str(args[0].month) + '-' + str(args[0].day)  + '-' + str(args[0].year) + '-' + '-'.join(args2)
            try:
            # try to get the cached result
                return stored_results[str_args]
            except KeyError:
            # nothing was cached for those args. let's fix that.
                result = stored_results[str_args] = method(*args)
            return result

        return memoized
    return inner_memo

def timeit(method):
    """ TODO make this just save the data and provide a function to
        print out timing stats"""
    @wraps(method)
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        print '%r %2.2f msec' % \
              (method.__name__, (te - ts) * 1000.0)
        return result

    return timed


def retry(method):
    """If at first you don't succeed, try, try again"""
    @wraps(method)
    def keep_on(*args, **kw):
        done = False
        counter = 0
        result = None
        while not done:
            try:
                result = method(*args, **kw)
                done = True
            except Exception as inst:
                traceback.print_stack()
                print "Jira connection error, retrying"
                time.sleep(45 + random.randint(0, 90))
                counter += 1
                if counter > 30:
                    print "Tried thirty times without luck."
                    done = True

        return result

    return keep_on
