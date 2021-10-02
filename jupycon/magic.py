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
        chunksize = CHUNKSIZE
        kwargs = {}
        for keyval in sline[1:]:
            key, value = keyval.split("=")
            if key == "chunksize":
                chunksize = value
            else:
                kwargs[key] = value
        #if there are any parameters, 1st parameter is always df
        if sline: 
            self.shell.user_ns[sline[0]] = query(cell.format_map(kwargs), chunksize)
            # return the result
            return f"Done! Result in {sline[0]}"
        else:
            return query(cell, chunksize)

def load_ipython_extension(ipython):
    ipython.register_magics(SqlMagics)
