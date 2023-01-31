"""
Core functional interface, querying the DB and helper functions
"""
import warnings

import pandas as pd
from sqlalchemy import text

from .config import JPConfig
from .defaults import REDSHIFT_CHUNKSIZE


jpc = JPConfig()


def change(name, configfile=None):
    """Change database to `name`"""
    jpc.change(name)


def query_raw(query_string):
    """
    Raw SQL, careful, you can break things here
    """
    with jpc.connect() as conn:
        return conn.execute(f"{query_string};")

    jpc.close_tunnel()


def query(query_str, chunksize=None):
    """
    Query the warehouse with a SELECT or WITH statement.

    returns:
        pandas.DataFrame
    """
    with jpc.connect() as conn:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            if chunksize:
                ret = pd.DataFrame()
                for chunk in pd.read_sql(text(query_str), conn, chunksize=chunksize):
                    ret = pd.concat([chunk, ret])
            else:
                ret = pd.read_sql(query_str, conn)

    jpc.close_tunnel()
    return ret


def list_schemas():
    """
    List all schemas
    returns:
        pandas.DataFrame
    """
    if jpc.dbtype == "redshift":
        return query(
            """select s.nspname as table_schema,
                      s.oid as schema_id,
                      u.usename as owner
               from pg_catalog.pg_namespace s
               join pg_catalog.pg_user u on u.usesysid = s.nspowner
               order by table_schema"""
        )
    elif jpc.dbtype == "bigquery":
        return query("select schema_name FROM INFORMATION_SCHEMA.SCHEMATA")

    elif jpc.dbtype == "databricks":
        return query("show schemas")
    else:
        raise NotImplementedError
        
        
def list_tables(schema):
    """
    List all tables in a schema

    returns:
        pandas.DataFrame
    """
    if jpc.dbtype == "redshift":
        return query(
            f"""
            select table_name, table_type
            from information_schema.tables t
            where t.table_schema = '{schema}'
            order by t.table_name"""
        )

    elif jpc.dbtype == "bigquery":
        return query(f"SELECT * FROM {schema}.INFORMATION_SCHEMA.TABLES")

    elif jpc.dbtype == "databricks":
        return query(f"show tables from {schema}")

    else:
        raise NotImplementedError

        
def list_columns(schema, table):
    """List all columns in a table.

    Args:
        schema (str): The name of the schema.
        table (str): The name of the table.

    Returns:
        pandas.DataFrame: A dataframe containing the columns in the table.

    Raises:
        NotImplementedError: If the function `list_columns` is not implemented for the current connection type.
    """
    # Check if the current connection type is "redshift"
    if jpc.dbtype == "redshift":
        import re

        # Regular expression pattern pull out comma delimited results (note: some values contain a comma).
        regex_pattern = r'\w+|\".+\"'
        
        # Execute SQL query to get the columns of the table
        # Source: https://docs.aws.amazon.com/redshift/latest/dg/PG_GET_COLS.html
        cols = query(f"select pg_get_cols('{schema}.{table}')")
        
        # Use the regular expression to extract the values from the query result
        df = pd.DataFrame([tuple(re.findall(regex_pattern, el)) for el in cols.pg_get_cols.values],
                          columns=["schema", "table", "column", "data_type", "index"])
        return df
    else:
        raise NotImplementedError(f"The function `list_columns` is not implemented for the connection type: {jpc.dbtype}.")
    

def df_to_table(dataframe, schema, table, chunksize=REDSHIFT_CHUNKSIZE):
    """
    Write pandas dataframe to the warehouse.
    """
    with jpc.connect() as conn:
        dataframe.to_sql(
            table,
            schema=schema,
            con=conn,
            index=False,
            if_exists="replace",
            chunksize=chunksize,
        )

    jpc.close_tunnel()


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
