import os

import pandas as pd
from sqlalchemy import create_engine, text
from sshtunnel import HandlerSSHTunnelForwarderError, SSHTunnelForwarder

from .defaults import REDSHIFT_CHUNKSIZE, LOCALHOST, REDSHIFT_PORT
from .config import JPTConfig


jbt = JPTConfig()

def _close_tunnel():
    if jbt.tunnel:
        jbt.tunnel.close()

def _conn():
    try:
        if jbt.tunnel:
            jbt.tunnel.start()

    except HandlerSSHTunnelForwarderError:
        print(f"Tunnel to {REDSHIFT_PORT} already opened, moving on...")

    return jbt.engine.connect()


def change(name):
    jbt.change(name)
    

def query_raw(query):
    """
    Raw querying
    """
    with _conn() as conn:
        return conn.execute(f"{query};")

    _close_tunnel()


def query(query, chunksize=REDSHIFT_CHUNKSIZE):
    """
    Query redshift.

    returns:
        pandas.DataFrame
    """
    with _conn() as conn:
        df = pd.DataFrame()
        for chunk in pd.read_sql(text(query), con=conn, chunksize=chunksize):
            df = pd.concat([chunk, df])

    _close_tunnel()
    return df


def list_schemas():
    """
    List all schemas

    returns:
        pandas.DataFrame
    """
    return query(
        """select s.nspname as table_schema,
                  s.oid as schema_id,
                  u.usename as owner
           from pg_catalog.pg_namespace s
           join pg_catalog.pg_user u on u.usesysid = s.nspowner
           order by table_schema"""
    )


def list_tables(schema):
    """
    List all tables in a schema

    returns:
        pandas.DataFrame
    """
    return query(
        f"""
        select table_name, table_type
        from information_schema.tables t
        where t.table_schema = '{schema}'
        order by t.table_name"""
    )


def df_to_table(df, schema, table, chunksize=REDSHIFT_CHUNKSIZE):
    """
    Write pandas dataframe to redshift.
    """
    with _conn() as conn:
        df.to_sql(
            table,
            schema=schema,
            con=conn,
            index=False,
            if_exists="replace",
            chunksize=chunksize,
        )

    _close_tunnel()


def peek(table, limit=3):
    return query(f"select * from {table} limit {limit}").T


def peek_schema(schema, limit=3):
    for table in list_tables(schema).table_name:
        data = peek(f"{schema}.{table}", limit)
        if not data.empty:
            print(table)
            print(f"-------------{data}\n")
