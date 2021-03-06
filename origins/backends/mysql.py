from __future__ import division, absolute_import
from . import _database

try:
    import pymysql as mysql
except ImportError:
    try:
        import MySQLdb as mysql
    except ImportError:
        raise ImportError('PyMySQL or mysql-python must be installed')


class Client(_database.Client):
    NUMERIC_TYPES = set([
        'bigint',
        'decimal',
        'double',
        'fixed',
        'float',
        'int',
        'integer',
        'mediumint',
        'numeric',
        'smallint',
        'tinyint',
    ])

    STRING_TYPES = set([
        'char',
        'longtext',
        'mediumtext',
        'nchar',
        'nvarchar',
        'text',
        'tinytext',
        'varchar',
    ])

    TIME_TYPES = set([
        'date',
        'datetime',
        'time',
        'timestamp',
        'year',
    ])

    BOOL_TYPES = set([
        'boolean',
    ])

    def __init__(self, database, **kwargs):
        self.name = database
        self.host = kwargs.get('host', 'localhost')
        self.port = kwargs.get('port', 3306)
        self.connect(user=kwargs.get('user'), password=kwargs.get('password'))

    def connect(self, user=None, password=None):
        self.connection = mysql.connect(db=self.name, host=self.host,
                                        port=self.port, user=user,
                                        passwd=password or '')

    def qn(self, name):
        return '`{}`'.format(name)

    def version(self):
        return self.fetchvalue('SELECT version()')

    def database(self):
        return {
            'name': self.name,
            'version': self.version(),
            'host': self.host,
            'port': self.port,
        }

    def tables(self):
        query = '''
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
            ORDER BY table_name
        '''

        keys = ('name',)

        tables = []
        for row in self.fetchall(query, [self.name]):
            tables.append(dict(zip(keys, row)))
        return tables

    def columns(self, table_name):
        query = '''
            SELECT column_name,
                ordinal_position,
                is_nullable,
                data_type
            FROM information_schema.columns
            WHERE table_schema = %s
                AND table_name = %s
            ORDER BY table_name, ordinal_position
        '''

        keys = ('name', 'index', 'nullable', 'type')

        columns = []
        for row in self.fetchall(query, [self.name, table_name]):
            attrs = dict(zip(keys, row))
            attrs['index'] -= 1
            if attrs['nullable'] == 'YES':
                attrs['nullable'] = True
            else:
                attrs['nullable'] = False
            columns.append(attrs)
        return columns

    def foreign_keys(self, table_name, column_name):
        try:
            self.connection.select_db('information_schema')
            query = '''
                SELECT
                    constraint_name,
                    referenced_table_name,
                    referenced_column_name
                FROM
                    key_column_usage
                WHERE
                    table_name = %s
                    AND column_name = %s
            '''
            keys = ('name', 'table', 'column')
            fks = []
            for row in self.fetchall(query, [table_name, column_name]):
                attrs = dict(zip(keys, row))
                fks.append(attrs)
            return fks
        finally:
            self.connection.select_db(self.name)


# Export class for API
Origin = _database.Database
