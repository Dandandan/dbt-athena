from collections import Iterable
from contextlib import contextmanager
from datetime import datetime
from getpass import getuser
import re

from dbt.adapters.base import Credentials
from dbt.adapters.sql import SQLConnectionManager
from dbt.compat import basestring, NUMBERS, to_string
from dbt.exceptions import RuntimeException
from dbt.logger import GLOBAL_LOGGER as logger

import sqlparse
from pyathenajdbc import connect

ATHENA_CREDENTIALS_CONTRACT = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'database': {
            'type': 'string',
        },
        'schema': {
            'type': 'string',
        },
        's3_staging_dir': {
            'type': 'string',
        },
        'region_name': {
            'type': 'string'
        }
    },
    'required': ['s3_staging_dir', 'database', 'schema', 'region_name'],
}


class AthenaCredentials(Credentials):
    SCHEMA = ATHENA_CREDENTIALS_CONTRACT
    ALIASES = {
        'catalog': 'database',
    }

    @property
    def type(self):
        return 'athena'

    def _connection_keys(self):
        return ('s3_staging_dir', 'database', 'schema', 'region_name')


class ConnectionWrapper(object):
    """Wrap a Athena connection in a way that accomplishes two tasks:

        - prefetch results from execute() calls so that presto calls actually
            persist to the db but then present the usual cursor interface
        - provide `cancel()` on the same object as `commit()`/`rollback()`/...

    """
    def __init__(self, handle):
        self.handle = handle
        self._cursor = None
        self._fetch_result = None

    def cursor(self):
        self._cursor = self.handle.cursor()
        return self

    def cancel(self):
        if self._cursor is not None:
            self._cursor.cancel()

    def close(self):
        # this is a noop on presto, but pass it through anyway
        self.handle.close()

    def commit(self):
        logger.debug("NotImplemented: commit")

    def rollback(self):
        logger.debug("NotImplemented: rollback")

    def fetchall(self):
        if self._cursor is None:
            return None

        if self._fetch_result is not None:
            ret = self._fetch_result
            self._fetch_result = None
            return ret

        return None

    def execute(self, sql, bindings=None):

        if bindings is not None:
            # presto doesn't actually pass bindings along so we have to do the
            # escaping and formatting ourselves
            bindings = tuple(self._escape_value(b) for b in bindings)
            sql = sql % bindings

        result = self._cursor.execute(sql)
        self._fetch_result = self._cursor.fetchall()
        return result

    @property
    def description(self):
        return self._cursor.description

    @classmethod
    def _escape_value(cls, value):
        """A not very comprehensive system for escaping bindings.

        I think "'" (a single quote) is the only character that matters.
        """
        if value is None:
            return 'NULL'
        elif isinstance(value, basestring):
            return "'{}'".format(value.replace("'", "''"))
        elif isinstance(value, NUMBERS):
            return value
        elif isinstance(value, datetime):
            time_formatted = value.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            return "TIMESTAMP '{}'".format(time_formatted)
        else:
            raise ValueError('Cannot escape {}'.format(type(value)))


class AthenaConnectionManager(SQLConnectionManager):
    TYPE = 'athena'

    @contextmanager
    def exception_handler(self, sql):
        try:
            yield
        # TODO: introspect into `DatabaseError`s and expose `errorName`,
        # `errorType`, etc instead of stack traces full of garbage!
        except Exception as exc:
            logger.debug("Error while running:\n{}".format(sql))
            logger.debug(exc)
            raise RuntimeException(to_string(exc))

    def add_begin_query(self):
        logger.debug("NotImplemented: add_begin_query")

    def add_commit_query(self):
        logger.debug("NotImplemented: add_commit_query")

    def commit(self, *args, **kwargs):
        logger.debug("NotImplemented: commit")

    def rollback(self, *args, **kwargs):
        logger.debug("NotImplemented: rollback")

    @classmethod
    def open(cls, connection):
        if connection.state == 'open':
            logger.debug('Connection is already open, skipping open.')
            return connection

        credentials = connection.credentials

        conn = connect(
            s3_staging_dir=credentials.s3_staging_dir,
            region_name=credentials.region_name
        )
        connection.state = 'open'
        connection.handle = ConnectionWrapper(conn)
        return connection

    @classmethod
    def get_status(cls, cursor):
        # this is lame, but the cursor doesn't give us anything useful.
        return 'OK'

    def cancel(self, connection):
        pass
        #connection.handle.cancel()

    def add_query(self, sql, auto_begin=True,
                  bindings=None, abridge_sql_log=False):

        connection = None
        cursor = None

        # TODO: is this sufficient? Largely copy+pasted from snowflake, so
        # there's some common behavior here we can maybe factor out into the
        # SQLAdapter?
        queries = [q.rstrip(';') for q in sqlparse.split(sql)]

        for individual_query in queries:
            # hack -- after the last ';', remove comments and don't run
            # empty queries. this avoids using exceptions as flow control,
            # and also allows us to return the status of the last cursor
            without_comments = re.sub(
                re.compile('^.*(--.*)$', re.MULTILINE),
                '', individual_query).strip()

            if without_comments == "":
                continue

            parent = super(AthenaConnectionManager, self)
            connection, cursor = parent.add_query(
                individual_query, auto_begin, bindings,
                abridge_sql_log
            )

        if cursor is None:
            raise RuntimeException(
                    "Tried to run an empty query on model '{}'. If you are "
                    "conditionally running\nsql, eg. in a model hook, make "
                    "sure your `else` clause contains valid sql!\n\n"
                    "Provided SQL:\n{}".format(connection.name, sql))

        return connection, cursor

    def execute(self, sql, auto_begin=False, fetch=False):
        _, cursor = self.add_query(sql, auto_begin)
        status = self.get_status(cursor)
        table = self.get_result_from_cursor(cursor)
        return status, table
