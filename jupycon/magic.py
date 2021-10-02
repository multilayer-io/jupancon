from IPython.core.magic import Magics, cell_magic, line_magic, magics_class

from .core import query
from .defaults import CHUNKSIZE


# The class MUST call this class decorator at creation time
@magics_class
class SqlMagics(Magics):
    @line_magic
    def select(self, line):
        """
        Simple line magic for SQL statements against redshift
        """
        return query(f"select {line}")

    @cell_magic
    def sql(self, line, cell):
        # 2 possible parameters: Name and Chunksize
        sline = line.split()
        # get the chunksize if provided, else get the default
        chunksize = CHUNKSIZE if len(sline) < 2 else int(sline[1])
        # point the result to the variable name in the user namespace
        self.shell.user_ns[sline[0]] = query(cell, chunksize)
        # return the result
        return f"Done! Result in {sline[0]}"


def load_ipython_extension(ipython):
    ipython.register_magics(SqlMagics)
