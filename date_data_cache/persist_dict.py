"""
Make a persistent dict with sqlite to have persistent memoization -- copied from StackOverflow

http://stackoverflow.com/questions/9320463/persistent-memoization-in-python
"""

from collections import MutableMapping
import sqlite3
import cPickle
import json
import zlib

import threading
import cache

_MAP_OF_CONNECTIONS = {}


class PersistentDict(MutableMapping):
    def __init__(self, dbpath, iterable=None, **kwargs):
        self.dbpath = dbpath
        with self.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute('create table if not exists memo '
                           '(key blob primary key not null, value blob not null)')
        if iterable is not None:
            self.update(iterable)
        self.mem_dict = cache.LRUCache(maxlen=1000000)
        self.mem_dict = {}
        self.update(kwargs)

    def encode(self, obj):
        try:
            rv = json.dumps(obj)
        except TypeError as e:
            rv = cPickle.dumps(obj)
        old_rv = rv
        try:
            rv = zlib.compress(rv)
        except:
            rv = old_rv
        return rv

    def decode(self, blob):
        old_blob = blob
        try:
            blob = zlib.decompress(str(blob))
        except:
            blob = old_blob
        try:
            rv = json.loads(str(blob))
        except:
            rv = cPickle.loads(str(blob))
        return rv

    def get_connection(self):
        key = self.dbpath + str(threading._get_ident())
        if key in _MAP_OF_CONNECTIONS:
            return _MAP_OF_CONNECTIONS[key]
        conn = sqlite3.connect(self.dbpath)
        print "Trying to open", self.dbpath
        _MAP_OF_CONNECTIONS[key] = conn
        return conn

    def __getitem__(self, key):
        key = str(key)
        if key in self.mem_dict:
            return self.mem_dict[key]
        with self.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute('select value from memo where key=?',
                           (key,))
            value = cursor.fetchone()
        if value is None:
            raise KeyError(key)
#       print 'returning ' + str(self.decode(value[0])) + ' for ' + key
        self.mem_dict[key] = self.decode(value[0])
        return self.mem_dict[key]

    def __setitem__(self, key, value):
        key = str(key)   # my keys are strings
        o_value = value
        value = self.encode(value)
        if key in self.mem_dict:
            old_value = self.mem_dict[key]
            if old_value == o_value:
                return
        self.mem_dict[key] = o_value
        with self.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute('insert or replace into memo values (?, ?)',
                           (key, sqlite3.Binary(value)))   # had to add the Binary wrapper

    def __delitem__(self, key):
        key = self.encode(key)
        if key in self.mem_dict:
            del self.mem_dict[key]
        with self.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                'select count(*) from memo where key=?',
                (key,))
            if cursor.fetchone()[0] == 0:
                raise KeyError(key)
            cursor.execute(
                'delete from memo where key=?',
                (key,))

    def __iter__(self):
        with self.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute('select key from memo')
            records = cursor.fetchall()
        for r in records:
            yield r[0]

    def iter_for_likes(self, likes):
        sql = ['select key from memo']
        if likes:
            sql[0] = sql[0] + " where"
        for l in likes:
            sql.append(" key like \'%" + l + "%\' and")
        sql = "".join(sql)
        if likes:
            sql = sql[:-3]
        print sql
        with self.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(sql + ";")
            record = cursor.fetchone()
            yield record[0]


    def __len__(self):
        with self.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute('select count(*) from memo')
            return cursor.fetchone()[0]

    def compress(self, key):
        v = self.__getitem__(key)
        del self.mem_dict[key]
        self.__setitem__(key, v)
