""" Place to keep utility decorators """

import time
import traceback
import random
import persist_dict
import pprint
from functools import wraps


def memo(method):
    """This is fairly generic for non-class functions"""
    name = "memo_" + method.__name__
    stored_results = persist_dict.PersistentDict('./' + name + '.sqlite')

    @wraps(method)
    def memoized(*args, **kw):
        args2 = [str(v) for v in args]
        str_args = method.__name__ + '-' + '-'.join(args2) + '-' + '-'.join(["%s-%s" % (k, v) for k, v in kw.items()])
        try:
        # try to get the cached result
            res = stored_results[str_args]
            # dangerous
            if "<Response [404]>" in str(res):
                raise KeyError('synthetic')
            return res
        except KeyError:
        # nothing was cached for those args. let's fix that.
            result = stored_results[str_args] = method(*args, **kw)
        return result

    return memoized


def memo_self_with_dates(method):
    """This is not generic - it assumes a class with a month and day members"""
    stored_results = persist_dict.PersistentDict('./memo_special.sqlite')

    @wraps(method)
    def memoized(*args):
        str_args = method.__name__ + '-' + str(args[0].month) + '-' + str(args[0].day)  + '-' + str(args[0].year) + '-' + '-'.join(args[1:])
        try:
        # try to get the cached result
            return stored_results[str_args]
        except KeyError:
        # nothing was cached for those args. let's fix that.
            result = stored_results[str_args] = method(*args)
        return result

    return memoized


def timeit(method):
    """ TODO make this just save the data and provide a function to
        print out timing stats"""
    @wraps(method)
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        print '%r %2.2f sec' % \
              (method.__name__, te - ts)
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
