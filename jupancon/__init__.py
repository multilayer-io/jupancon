"""Jupancon, connector to several DBs that returns pandas. Magic included."""

__version__ = "0.1.1"


from .core import (
    query_raw,
    list_schemas,
    list_tables,
    query,
    df_to_table,
    peek,
    peek_schema,
    change,
)


# snippet to check if the environment is interactive
def is_interactive():
    import __main__ as main

    return not hasattr(main, "__file__")


def load_magics():
    if is_interactive():
        from .magic import load_ipython_extension
        from IPython import get_ipython

        load_ipython_extension(get_ipython())
        print("SQL magics loaded!")
    else:
        print("Non interactive environment detected, no magics loaded")


__version__ = "0.3.0"
