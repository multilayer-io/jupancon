"""Jupancon, connector to several DBs that returns pandas. Magic included."""

__version__ = "0.2.1"


from .core import (change, df_to_table, list_schemas, list_tables, peek,
                   peek_schema, query, query_raw)


# snippet to check if the environment is interactive
def is_interactive():
    import __main__ as main

    return not hasattr(main, "__file__")


def load_magics():
    if is_interactive():
        from IPython import get_ipython

        from .magic import load_ipython_extension

        load_ipython_extension(get_ipython())
        print("SQL magics loaded!")
    else:
        print("Non interactive environment detected, no magics loaded")
