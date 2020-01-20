from collections import Iterable
from contextlib import contextmanager
from datetime import datetime
from getpass import getuser
import re
import decimal
from dataclasses import dataclass
from typing import Tuple, Optional

from dbt.adapters.base import Credentials
from dbt.adapters.sql import SQLConnectionManager
from dbt.exceptions import RuntimeException
from dbt.logger import GLOBAL_LOGGER as logger

import sqlparse
from pyathena import connect
from pyathena.async_cursor import AsyncCursor
from pyathena.error import OperationalError
from pyathena.model import AthenaQueryExecution


@dataclass
class AthenaCredentials(Credentials):
    database: str
    schema: str
    s3_staging_dir: str
    region_name: str
    threads: int = 1

    _ALIASES = {
        'catalog': 'database'
    }

    @property
    def type(self) -> str:
        return 'athena'

    def _connection_keys(self) -> Tuple[str]:
        return ('s3_staging_dir', 'database', 'schema', 'region_name')


class CursorWrapper(object):
    def __init__(self, cursor):
        self._cursor = cursor
        self._query_id = None
        self._fetch_result = None
        self._state = None

    def fetchall(self):
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

        query_id, future = self._cursor.execute(sql)
        result_set = future.result()

        if result_set.state != AthenaQueryExecution.STATE_SUCCEEDED:
            raise OperationalError(result_set.state_change_reason)

        self._fetch_result = result_set.fetchall()
        self._query_id = query_id
        self._state = result_set.state
        return self

    @property
    def description(self):
        return self._cursor.description(self._query_id).result()

    @property
    def state(self):
        return self._state

    @classmethod
    def _escape_value(cls, value):
        """A not very comprehensive system for escaping bindings.

        I think "'" (a single quote) is the only character that matters.
        """
        if value is None:
            return 'NULL'
        elif isinstance(value, str):
            return "'{}'".format(value.replace("'", "''"))
        elif isinstance(value, (int,float,decimal.Decimal)):
            return value
        elif isinstance(value, datetime):
            time_formatted = value.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            return "TIMESTAMP '{}'".format(time_formatted)
        else:
            raise ValueError('Cannot escape {}'.format(type(value)))


class ConnectionWrapper(object):
    """Wrap a Athena connection in a way that accomplishes two tasks:

        - prefetch results from execute() calls so that presto calls actually
            persist to the db but then present the usual cursor interface
        - provide `cancel()` on the same object as `commit()`/`rollback()`/...

    """
    def __init__(self, handle, max_workers: int):
        self.handle = handle
        # TODO: make it configurable through Athena credentials!
        self._cursor = handle.cursor(max_workers=max_workers)

    def cursor(self):
        return CursorWrapper(self._cursor)

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


class AthenaConnectionManager(SQLConnectionManager):
    TYPE = 'athena'

    @contextmanager
    def exception_handler(self, sql: str):
        try:
            yield
        # TODO: introspect into `DatabaseError`s and expose `errorName`,
        # `errorType`, etc instead of stack traces full of garbage!
        except Exception as exc:
            logger.debug("Error while running:\n{}".format(sql))
            logger.debug(exc)
            raise RuntimeException(str(exc))

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
            region_name=credentials.region_name,
            schema_name=credentials.database,
            cursor_class=AsyncCursor
        )
        connection.state = 'open'
        connection.handle = ConnectionWrapper(conn, credentials.threads)
        return connection

    @classmethod
    def get_status(cls, cursor):
        if cursor.state == AthenaQueryExecution.STATE_SUCCEEDED:
            return 'OK'
        else:
            return 'ERROR'

    def cancel(self, connection):
        connection.handle.cancel()

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
