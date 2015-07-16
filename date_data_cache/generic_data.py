"""
Make a sqlite DB to handle 2 types of extra data: per app and per
app/host They have a data type (string or number) and also
characteristics for reductions (total/max/avg or concat/count)
"""

import sqlite3
import collections

import threading

_MAP_OF_CONNECTIONS_1_KEY = {}
_MAP_OF_CONNECTIONS_2_KEYS = {}

def get_data_type_name(value):
    if isinstance(value, (int, long, float, complex)):
        return 'numeric'
    return 'text'
    
def get_fields(connection, tb_name):
    a = connection.cursor().execute("select sql from sqlite_master where type='table' and name=?",
                                    (tb_name,))
    sql = a.fetchall()[0][0]
    print sql
    left_paren = sql.find("(")
    left_left_paren = left_paren + sql[left_paren + 1:].find("(")
    right_paren = sql.rfind(")")
    right_right_paren = right_paren + sql[right_paren + 1:].find(")")
    sql = sql[0:left_left_paren - 1] + sql[right_right_paren:]
    left_paren = sql.find("(")
    right_paren = sql.rfind(")")
    fields = [g.split(' ')[0] for g in [f.strip(' ') for f in sql[left_paren + 1:right_paren + 1].split(",")[0:-1] ]]
    return fields
    

class PersistentData(object):
    def __init__(self, dbpath_1, dbpath_2):
        self.dbpath_1 = dbpath_1
        self.dbpath_2 = dbpath_2
        self.mem_dict = collections.defaultdict(lambda: collections.defaultdict(str))
        connection = self.get_connection_1()
        cursor = connection.cursor()
        cursor.execute('create table if not exists app_data '
                       '(key_1 text not null, date_string text, primary key (key_1, date_string))')
        self.db_names_1 = get_fields(connection, 'app_data')

        connection = self.get_connection_2()
        cursor = connection.cursor()
        cursor.execute('create table if not exists app_host_data '
                       '(key_1 text not null, key_2 text not null, date_string text, primary key (key_1, key_2, date_string))')
        self.db_names_2 = get_fields(connection, 'app_host_data')

    def add_field_2(self, name, value):
        connection = self.get_connection_2()
        cursor = connection.cursor()
        type_name = get_data_type_name(value)
        cursor.execute('alter table app_host_data add column {} {}'.format(name, type_name))
        self.db_names_2 = get_fields(connection, 'app_data')

    def add_field_1(self, name, value):
        connection = self.get_connection_1()
        cursor = connection.cursor()
        type_name = get_data_type_name(value)
        cursor.execute('alter table app_data add column {} {}'.format(name, type_name))
        self.db_names_1 = get_fields(connection, 'app_data')

    def get(self, key_1, key_2 = None, name = None, date_string = None):
        if key_2:
            key = str(key_1) + str(key_2)
            if name not in self.db_names_2:
                raise KeyError('field {} not in db'.format(name))
        else:
            key = str(key_1)
            if name not in self.db_names_1:
                raise KeyError('field {} not in db'.format(name))
        if key in self.mem_dict:
            return self.mem_dict[key][name]
        if key_2:
            with self.get_connection_2() as connection:
                cursor = connection.cursor()
                cursor.execute('select {} from app_host_data where key_1=?, key_2=?, date_string=?'.foramt(name),
                               (key_1, key_2, date_string or '',))
            value = cursor.fetchone()
        else:
            with self.get_connection_1() as connection:
                cursor = connection.cursor()
                cursor.execute('select {} from app_data where key_1=?, date_string=?'.foramt(name),
                               (key_1, date_string or '',))
            value = cursor.fetchone()
        if value is None:
            raise KeyError(key)
        self.mem_dict[key][name] = value[0]
        return self.mem_dict[key][name]

    def get_connection_1(self):
        key = self.dbpath_1 + str(threading._get_ident())
        if key in _MAP_OF_CONNECTIONS_1_KEY:
            return _MAP_OF_CONNECTIONS_1_KEY[key]
        conn = sqlite3.connect(self.dbpath_1)
        print "Trying to open", self.dbpath_1
        _MAP_OF_CONNECTIONS_1_KEY[key] = conn
        return conn

    def get_connection_2(self):
        key = self.dbpath_2 + str(threading._get_ident())
        if key in _MAP_OF_CONNECTIONS_2_KEYS:
            return _MAP_OF_CONNECTIONS_2_KEYS[key]
        conn = sqlite3.connect(self.dbpath_2)
        print "Trying to open", self.dbpath_2
        _MAP_OF_CONNECTIONS_2_KEYS[key] = conn
        return conn

    def set(self, key_1, key_2 = None, name = None, value = None, date_string = None):
        if key_2:
            key = str(key_1) + str(key_2)   # my keys are strings
            if name not in self.db_names_2:
                self.add_field_2(name, value)
        else:
            key = str(key_1)
            if name not in self.db_names_1:
                self.add_field_1(name, value)
        o_value = value
        if key in self.mem_dict:
            old_value = self.mem_dict[key][name]
            if old_value == o_value:
                return
        self.mem_dict[key][name] = o_value
        if key_2:
            with self.get_connection_2() as connection:
                cursor = connection.cursor()
                cursor.execute('insert or replace into app_host_data (key_1, key_2, date_string, {0}) values (?, ?, ?, ?)'.format(name),
                               (key_1, key_2, date_string or '', value))
        else:
            with self.get_connection_1() as connection:
                cursor = connection.cursor()
                cursor.execute('insert or replace into app_data (key_1, date_string, {0}) values (?, ?, ? )'.format(name),
                               (key_1, date_string or '', value))
            


if __name__ == '__main__':
    a = PersistentData('store_1', 'store_2')
    a.set("fooserv", "vnccloud30b", "memory", 343043, '2015-7-15')
    print a.get("fooserv", "vnccloud30b", "memory", '2015-7-15')
    a.set("fooserv", None, "version", 1343434.5, '2015-7-15')
    print a.get("fooserv", None, "version", '2015-7-15')
