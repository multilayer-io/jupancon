from databricks import sql


class DatabricksEngine(object):
    # there is no good sqlalchemy engine yet
    def __init__(self, hostname, http_path, catalog, token):
        self.hostname = hostname
        self.http_path = http_path
        self.catalog = catalog
        self.token = token

    def connect(self):
        return sql.connect(
              server_hostname=self.hostname,
              http_path=self.http_path,
              catalog=self.catalog,
              access_token=self.token
        )