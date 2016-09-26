from django.db import connections


def get_named_connection(using='default'):
    """
    Returns the connection for the argument database.  The unit tests, however, need
    to return the same database connection for 'default' and 'read'.  In this function,
    just return the default database any any requested database to make the unit tests
    happy.

    @param using: database connection label
    @return: database connection object
    """
    from django.conf import settings
    if settings.TESTING:
        using = 'default'
    return connections[using]


def sql_execute(sql_query, sql_args=None, using='default'):
    """
    Executes and returns all the rows in a SQL query.  This should only
    be used when the number of results is expected to be small.

    @param sql_query: raw SQL query for database
    @param sql_args: iterable of database arguments
    @param using: database connection label
    @return: None
    """
    cursor = get_named_connection(using).cursor()
    try:
        cursor.execute(sql_query, sql_args)
    finally:
        cursor.close()


def sql_execute_fetchall(sql_query, sql_args=None, using='default'):
    """
    Executes and returns all the rows in a SQL query.  This should only
    be used when the number of results is expected to be small.

    @param sql_query: raw SQL query for database
    @param sql_args: iterable of database arguments
    @param using: database connection label
    @return: list of SQL query result rows
    """
    cursor = get_named_connection(using).cursor()
    try:
        cursor.execute(sql_query, sql_args)
        rows = cursor.fetchall()
        return rows
    finally:
        cursor.close()


def server_side_cursor_fetchall(sql_query, sql_args=None, chunk_size=5000, using='default'):
    """
    Generator that iterates through rows of a SQL query using a server-side cursor.
    Fetches rows in chunks for performance.  This is for Postgres only.  A version
    for MySQL is needed.

    @param sql_query: The query to execute.
    @param chunk_size: The number of rows to fetch in a single chunk.
    """
    sql = 'DECLARE ssc CURSOR FOR {}'.format(sql_query, sql_args)
    sql_fetch_chunk = 'FETCH {} FROM ssc'.format(chunk_size)
    cursor = get_named_connection(using).cursor()

    try:
        cursor.execute('BEGIN TRANSACTION ISOLATION LEVEL READ COMMITTED READ ONLY')
        cursor.execute(sql)
        try:
            cursor.execute(sql_fetch_chunk)
            while True:
                rows = cursor.fetchall()
                if not rows:
                    break
                for row in rows:
                    yield row
                cursor.execute(sql_fetch_chunk)
        finally:
            cursor.execute('CLOSE ssc')
    finally:
        cursor.close()


def server_side_cursor_fetchall_column_descriptions(sql_query, sql_args=None, chunk_size=5000, using='default'):
    """
    Generator that iterates through rows of a SQL query using a server-side cursor.
    Fetches rows in chunks for performance.  This is for Postgres only.

    @param sql_query: The query to execute.
    @param chunk_size: The number of rows to fetch in a single chunk.
    @return: (column_description, row_iter)
    """
    sql = 'DECLARE ssc CURSOR FOR {}'.format(sql_query, sql_args)
    sql_fetch_chunk = 'FETCH {} FROM ssc'.format(chunk_size)
    cursor = connections[using].cursor()

    try:
        cursor.execute('BEGIN TRANSACTION')
        cursor.execute(sql)
        cursor.execute(sql_fetch_chunk)
    except Exception:
        cursor.close()
        raise

    def row_iter():
        try:
            while True:
                rows = cursor.fetchall()
                if not rows:
                    break
                for row in rows:
                    yield row
                cursor.execute(sql_fetch_chunk)
        finally:
            cursor.execute('CLOSE ssc')
            cursor.close()

    return cursor.description, row_iter()

