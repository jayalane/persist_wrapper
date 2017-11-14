#! /bin/env python

"""
   Uses the caching stuff to cache URLs called with requests
   Not adding requests as formal requirement, it'll just fail 
"""

import os
import re

import datetime

import requests
import json
import decorators
import collections

import gevent
import gevent.event

_THE_PRINT_CONFIG = False

_THROTTLED_CALLS = []
_THROTTLED_ANSWERS = {}
_THROTTLED_GLET = None


# now some caching of the CAL reports

_DATE_RE = re.compile(r'startTime=([0-9]+)&')
_EPOCH = datetime.datetime.utcfromtimestamp(0)


def unix_time_millis(dt):
    return int((dt - _EPOCH).total_seconds() * 1000.0)


def sherlock_start_end_time_string_from_date_time(m, d, y, hour=None):
    if hour is None:
        dt1 = datetime.datetime(y, m, d, 0, 0)
        dt2 = dt1 + datetime.timedelta(1)
    else:
        dt1 = datetime.datetime(y, m, d, hour, 0)
        dt2 = dt1 + datetime.timedelta(hours=1)
    return "startTime={0}&endTime={1}".format(unix_time_millis(dt1),
                                              unix_time_millis(dt2))


def date_from_cache(str_args):
    # given a CAL2 URL return the date it's for
    seconds = 0
    s = re.search(_DATE_RE, str_args)
    if s:
        seconds = int(s.group(1)) / 1000.0
    return datetime.datetime.utcfromtimestamp(seconds)


def should_not_cache(res, str_args):
    # persist callback to see if we should use the cached value
    try:
        if '404' in repr(res) and \
               datetime.date.today() - date_from_cache(str_args) < datetime.timedelta(5):
            # use a 404 unless it's new
            return True
    except:
        pass
    try:
        data = json.loads(res._content)
        if len(res._content) < 700:
            if _THE_PRINT_CONFIG:
                print "No data, skipping cache if "
            if 'tsdb' in str_args:
                if _THE_PRINT_CONFIG:
                    print " from TSDB"
                return True
            if datetime.date.today() - date_from_cache(str_args) < datetime.timedelta(35):
                if _THE_PRINT_CONFIG:
                    print "recent"
                return True
        if _THE_PRINT_CONFIG:
            print "len is", len(res._content)
    except Exception as e:
        print "Exception", repr(e)
        pass
    return False


def process_throttled_urls():
    while 1:
        try:
            url, event = _THROTTLED_CALLS.pop()
            print url 
            a = real_requests_get(url)
            _THROTTLED_ANSWERS[url] = a
            event.set()
        except IndexError:
            gevent.sleep(0.01)


@decorators.memo(check_func=should_not_cache, mem_cache=False, cache_none=False)
def requests_get(url):
    global _THROTTLED_GLET
    if _THROTTLED_GLET is None or _THROTTLED_GLET.ready():
        _THROTTLED_GLET = gevent.spawn(process_throttled_urls)
    a = None
    while not a:
        event = gevent.event.Event()
        event.clear()
        if _THE_PRINT_CONFIG:
            print "Enqueueing call for", url, "len is", len(_THROTTLED_CALLS)
        _THROTTLED_CALLS.append((url, event))
        event.wait(timeout=30.0)
        if _THE_PRINT_CONFIG:
            print "Dequeue call for", url
        a = _THROTTLED_ANSWERS.get(url, None)
    return a

@decorators.memo(check_func=should_not_cache, mem_cache=False, cache_none=False)
@decorators.retry
def real_requests_get(url):
    headers = {'Content-Type': 'application/json',
               'Accept': 'application/json'}
    if _THE_PRINT_CONFIG:
        print "Actually calling ", url
    r = requests.get(url, headers=headers)
    if r is not None and hasattr(r, 'status_code') and _THE_PRINT_CONFIG:
        print "got", r.status_code, "for", url
        if r.status_code > 399:
            print r._content
    last_log = len(r._content)
    if _THE_PRINT_CONFIG:
        print "Len", last_log
    return r

if __name__ == "__main__":
    print requests_get("http://disputingtaste.com/").body
