import os

import pandas as pd
from sqlalchemy import create_engine, text
from sshtunnel import HandlerSSHTunnelForwarderError, SSHTunnelForwarder

from .defaults import REDSHIFT_CHUNKSIZE, LOCALHOST, REDSHIFT_PORT

# TODO try/catch this for missing envs

use_bastion = os.getenv("USE_BASTION", default=False)
host = LOCALHOST if use_bastion else os.getenv("REDSHIFT_HOST")
engine = create_engine(
    "redshift+psycopg2://"
    f"{os.getenv('REDSHIFT_USER')}:{os.getenv('REDSHIFT_PASS')}"
    f"@{host}:{REDSHIFT_PORT}/{os.getenv('REDSHIFT_DB')}",
    connect_args={"sslmode": "prefer"},
)

# Opens tunnel, but only if the port is free
try:
    if use_bastion:
        tunnel = SSHTunnelForwarder(
            os.getenv("BASTION_SERVER"),
            ssh_username=os.getenv("BASTION_USER"),
            remote_bind_address=(os.getenv("REDSHIFT_HOST"), REDSHIFT_PORT),
            local_bind_address=(LOCALHOST, REDSHIFT_PORT),
        )
        tunnel.start()
        print("SSH tunnel went through, stopping")
        tunnel.close()

    else:
        tunnel = None
except HandlerSSHTunnelForwarderError:
    # TODO proper logs
    tunnel = None
    print(
        "Couldn't open SSH tunnel to Bastion. "
        "Assuming tunnel is already open, will not try again."
        "Restart Kernel to retry."
    )


def _close_tunnel():
    if tunnel:
        tunnel.close()


def _conn():
    try:
        if tunnel:
            tunnel.start()

    except HandlerSSHTunnelForwarderError:
        print(f"Tunnel to {REDSHIFT_PORT} already opened, moving on...")

    return engine.connect()


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
