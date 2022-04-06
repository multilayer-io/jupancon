"""
Core functional interface, querying the DB and helper functions
"""
import pandas as pd
from sqlalchemy import text

from .config import JPTConfig
from .defaults import REDSHIFT_CHUNKSIZE

jpt = JPTConfig()


def change(name, configfile=None):
    """Change database to `name`"""
    jpt.change(name)


def query_raw(query_string):
    """
    Raw SQL, careful, you can break things here
    """
    with jpt.connect() as conn:
        return conn.execute(f"{query_string};")

    jpt.close_tunnel()


def query(query_str, chunksize=REDSHIFT_CHUNKSIZE):
    """
    Query redshift.

    returns:
        pandas.DataFrame
    """
    with jpt.connect() as conn:
        ret = pd.DataFrame()
        for chunk in pd.read_sql(text(query_str), conn, chunksize=chunksize):
            ret = pd.concat([chunk, ret])

    jpt.close_tunnel()
    return ret


def list_schemas():
    """
    List all schemas

    returns:
        pandas.DataFrame
    """
    if jpt.dbtype == "redshift":
        return query(
            """select s.nspname as table_schema,
                      s.oid as schema_id,
                      u.usename as owner
               from pg_catalog.pg_namespace s
               join pg_catalog.pg_user u on u.usesysid = s.nspowner
               order by table_schema"""
        )
    if jpt.dbtype == "bigquery":
        return query("select schema_name FROM INFORMATION_SCHEMA.SCHEMATA")

    raise NotImplementedError


def list_tables(schema):
    """
    List all tables in a schema

    returns:
        pandas.DataFrame
    """
    if jpt.dbtype == "redshift":
        return query(
            f"""
            select table_name, table_type
            from information_schema.tables t
            where t.table_schema = '{schema}'
            order by t.table_name"""
        )

    if jpt.dbtype == "bigquery":
        return query(f"SELECT * FROM {schema}.INFORMATION_SCHEMA.TABLES")

    raise NotImplementedError


def df_to_table(dataframe, schema, table, chunksize=REDSHIFT_CHUNKSIZE):
    """
    Write pandas dataframe to redshift.
    """
    with jpt.connect() as conn:
        dataframe.to_sql(
            table,
            schema=schema,
            con=conn,
            index=False,
            if_exists="replace",
            chunksize=chunksize,
        )

    jpt.close_tunnel()


def peek(table, limit=3):
    """
    Look at the first few lines of your dataset
    transposed, so all table columns fit the screen
    nicely.
    """
    return query(f"select * from {table} limit {limit}").T


def peek_schema(schema, limit=3):
    """
    Explore a whole schema by doing peek(table) in every table.
    """
    for table in list_tables(schema).table_name:
        data = peek(f"{schema}.{table}", limit)
        if not data.empty:
            print(table)
            print(f"-------------{data}\n")
