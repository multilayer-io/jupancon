import re

from IPython.core.magic import Magics, cell_magic, line_magic, magics_class

from .core import query
from .defaults import REDSHIFT_CHUNKSIZE


# The class MUST call this class decorator at creation time
@magics_class
class SqlMagics(Magics):
    @line_magic
    def select(self, line):
        """
        Line magic for SQL statements that return data
        """
        return query(f"select {line}")

    @line_magic
    def SELECT(self, line):
        """
        Line magic for SQL statements that return data (SHOUTING EDITION)
        """
        return self.select(line)

    @cell_magic
    def sql(self, line, cell):
        """
        Cell magic for SQL statements that return data
        """
        # regex to split parameters line using spaces without breaking strings
        sline = re.compile(r"""((?:[^ "']|"[^"]*"|'[^']*')+)""").split(line)[1::2]
        kwargs = {}
        for keyval in sline[1:]:
            key, value = keyval.split("=")
            kwargs[key] = value
        # if there are any parameters, 1st parameter is always df
        if sline:
            # first parameter is the DataFrame rest are mapped against the string
            self.shell.user_ns[sline[0]] = query(
                cell.format_map(kwargs), REDSHIFT_CHUNKSIZE
            )
            # return the result
            return f"Done! Result in {sline[0]}"
        else:
            # if no parameters, return DataFrame as output in the cell
            return query(cell, REDSHIFT_CHUNKSIZE)


def load_ipython_extension(ipython):
    ipython.register_magics(SqlMagics)
