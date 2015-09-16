"""
Make a sqlite DB to handle 2 types of extra data: per app and per
app/host They have a data type (string or number) and also
characteristics for reductions (total/max/avg or concat/count)
"""

import sqlite3
import collections

import threading

_MAP_OF_CONNECTIONS_KEY = {}

def get_data_type_name(value):
    if isinstance(value, (int, long, float, complex)):
        return 'numeric'
    return 'text'
    
def get_fields(connection, tb_name, debug_sql = False):
    a = connection.cursor().execute("select sql from sqlite_master where type='table' and name=?",
                                    (tb_name,))
    sql = a.fetchall()[0][0]
    if debug_sql:
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
    def __init__(self, name, debug_sql = False):
        self.debug_sql = debug_sql
        self.dbpath = "data_" + name + ".sql"
        self.mem_dict = collections.defaultdict(lambda: collections.defaultdict(str))
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute('create table if not exists app_data '
                       '(key_1 text not null, date_string text not null, primary key (key_1, date_string))')
        self.db_names_1 = get_fields(connection, 'app_data')

        cursor = connection.cursor()
        cursor.execute('create table if not exists app_host_data '
                       '(key_1 text not null, key_2 text not null, date_string text not null, primary key (key_1, key_2, date_string))')
        self.db_names_2 = get_fields(connection, 'app_host_data')


    def add_field_2(self, name, value):
        connection = self.get_connection()
        cursor = connection.cursor()
        type_name = get_data_type_name(value)
        the_sql = 'alter table app_host_data add column {} {}'.format(name, type_name)
        if self.debug_sql:
            print the_sql
        cursor.execute(the_sql)
        self.db_names_2 = get_fields(connection, 'app_host_data')

    def add_field_1(self, name, value):
        connection = self.get_connection()
        cursor = connection.cursor()
        type_name = get_data_type_name(value)
        the_sql = 'alter table app_data add column {} {}'.format(name, type_name)
        if self.debug_sql:
            print the_sql
        cursor.execute(the_sql)
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
#       if key in self.mem_dict:
#            return self.mem_dict[key][name]
        value = None
        with self.get_connection() as connection:
            cursor = connection.cursor()
            if key_2:
                the_sql = 'select {} from app_host_data where key_1=? and key_2=? and date(date_string) >= date(?) order by date(date_string) limit 1'.format(name)
                if self.debug_sql:
                    print the_sql
                cursor.execute(the_sql, 
                               (key_1, key_2, date_string or '2015-01-01',))
            else:
                the_sql = 'select {} from app_data where key_1=? and date(date_string) >= date(?) order by date(date_string) limit 1'.format(name)
                if self.debug_sql:
                    print the_sql
                cursor.execute(the_sql, (key_1, date_string or '2015-01-01',))
            value = cursor.fetchone()
        if value is None:
            raise KeyError(key)
        self.mem_dict[key][name] = value[0]
        return self.mem_dict[key][name]

    def get_connection(self):
        key = self.dbpath + str(threading._get_ident())
        if key in _MAP_OF_CONNECTIONS_KEY:
            return _MAP_OF_CONNECTIONS_KEY[key]
        conn = sqlite3.connect(self.dbpath)
        print "Trying to open", self.dbpath
        _MAP_OF_CONNECTIONS_KEY[key] = conn
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
        with self.get_connection() as connection:
            if key_2:
                cursor = connection.cursor()
                cursor.execute('insert or replace into app_host_data (key_1, key_2, date_string, {0}) values (?, ?, ?, ?)'.format(name),
                               (key_1, key_2, date_string or '2015-01-01', value))
            else:
                cursor = connection.cursor()
                cursor.execute('insert or replace into app_data (key_1, date_string, {0}) values (?, ?, ? )'.format(name),
                               (key_1, date_string or '2015-01-01', value))
            


if __name__ == '__main__':
    a = PersistentData('store_1')
    a.set("fooserv", "vnccloud30b", "memory", 343043, '2015-07-15')
    print a.get("fooserv", "vnccloud30b", "memory", '2015-07-15')
    a.set("fooserv", None, "version", 1343434.5, '2015-07-15')
    print a.get("fooserv", None, "version", '2015-07-15')
