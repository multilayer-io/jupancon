import os
import yaml
from pathlib import Path
from collections import defaultdict

from sqlalchemy import create_engine, text
from sshtunnel import HandlerSSHTunnelForwarderError, SSHTunnelForwarder

from .defaults import CONFIG_PATH, LOCALHOST, REDSHIFT_PORT

# TODO Proper logs

class JPTConfig(object):
    """
    Jupancon Configuration Class - Like a factory pattern for SQLAlchemy engines & SSH tunnels, 
    but without the overengineering.
    """
    def _load_config_yaml(self, name=None):
        path = f'{Path.home()}/{CONFIG_PATH}'
        if os.path.exists(path):
            with open(path) as config_file:

                try:
                    fullfile = yaml.safe_load(config_file)
                    if "default" in fullfile.keys() and not name:
                        name = fullfile["default"]

                    return defaultdict(bool, fullfile[name])

                except KeyError:
                    print(f"{name} not found in {path}")            
        
        
    def _get_engine_tunnel(self, config):
        # TODO try/catch this for missing config/envs
        self.use_bastion = os.getenv("JPC_USE_BASTION", default=config["use_bastion"])
        self.host = LOCALHOST if self.use_bastion else os.getenv("JPC_HOST", default=config["host"])
        self.port = config['port'] if config['port'] else REDSHIFT_PORT
        self.dbtype = os.getenv("JPC_DB_TYPE", default=config["type"]) 
        self.user = os.getenv('JPC_USER', default=config['user'])
        if self.dbtype == 'redshift':
            self.engine = create_engine(
                "redshift+psycopg2://"
                f"{self.user}:{os.getenv('JPC_PASS', default=config['pass'])}"
                f"@{self.host}:{self.port}/{os.getenv('JPC_DB', default=config['dbname'])}",
                connect_args={"sslmode": "prefer"},
            )
        elif self.dbtype == 'bigquery':
            self.engine = create_engine(f"bigquery://{os.getenv('JPC_GCP_PROJECT', default=config['project'])}")
        else:
            raise NotImplementedError
        # Opens tunnel, but only if the port is free and we are using bastion
        try:
            if self.use_bastion:
                print("Using Bastion, testing SSH tunnel...")
                self.tunnel = SSHTunnelForwarder(
                    os.getenv("JPC_BASTION_SERVER", default=config["bastion_server"]),
                    ssh_username=os.getenv("JPC_BASTION_USER", default=config["bastion_user"]),
                    remote_bind_address=(os.getenv("JPC_BASTION_HOST", default=config["bastion_host"]), REDSHIFT_PORT),
                    local_bind_address=(LOCALHOST, REDSHIFT_PORT),
                )
                self.tunnel.start()
                print("SSH tunnel works!")
                self.tunnel.close()            
            else:
                self.tunnel = None
                
        except HandlerSSHTunnelForwarderError:
            self.tunnel = None
            print(
                "Couldn't open SSH tunnel to Bastion. "
                "Assuming tunnel is already open, will not try again."
                "Restart Kernel to retry."
            ) 

    def __init__(self):
         self._get_engine_tunnel(self._load_config_yaml())
     
    
    def change(self, name):
        self._get_engine_tunnel(self._load_config_yaml(name))
  

            




