"""
Jupancon Configuration.

This module handles the engine and SSH tunnels connecting to the
DB of choice.
"""

import os
from collections import defaultdict
from pathlib import Path

import yaml
from sqlalchemy import create_engine
from sshtunnel import HandlerSSHTunnelForwarderError, SSHTunnelForwarder

from .defaults import CONFIG_PATH, LOCALHOST, REDSHIFT_PORT

# TODO Proper logs


class JPTConfig:
    """
    Jupancon Configuration Class - Like a factory pattern for SQLAlchemy
    engines & SSH tunnels, but without the overengineering.
    """

    def _load_config_yaml(self, name=None, configfile=None):
        """Loads the config YAML file for a particular DB, if specified"""
        path = configfile if configfile else f"{Path.home()}/{CONFIG_PATH}"
        if os.path.exists(path):
            with open(path, "r") as config_file:
                yaml_config = yaml.safe_load(config_file)
                try:
                    if "default" in yaml_config.keys() and not name:
                        name = yaml_config["default"]

                    self.name = name
                    return defaultdict(bool, yaml_config[name])

                except KeyError:
                    print(f"{name} not found in {path}")

        return defaultdict(bool)

    def _get_engine_tunnel(self, config):
        # TODO try/catch this for missing config/envs
        self.use_bastion = os.getenv("JPC_USE_BASTION", default=config["use_bastion"])
        self.host = (
            LOCALHOST
            if self.use_bastion
            else os.getenv("JPC_HOST", default=config["host"])
        )
        self.port = config["port"] if config["port"] else REDSHIFT_PORT
        self.dbtype = os.getenv("JPC_DB_TYPE", default=config["type"])
        self.user = os.getenv("JPC_USER", default=config["user"])
        self.dbname = os.getenv("JPC_DB", default=config["dbname"])
        if self.dbtype == "redshift":
            self.engine = create_engine(
                "redshift+psycopg2://"
                f"{self.user}:{os.getenv('JPC_PASS', default=config['pass'])}"
                f"@{self.host}:{self.port}/{self.dbname}",
                connect_args={"sslmode": "prefer"},
            )
        elif self.dbtype == "bigquery":
            self.project = os.getenv("JPC_GCP_PROJECT", default=config["project"])
            self.engine = create_engine(f"bigquery://{self.project}")
        elif not self.dbtype:
            raise Exception(f"{self.name} not found")
        else:
            raise NotImplementedError
        # Opens tunnel, but only if the port is free and we are using bastion
        try:
            if self.use_bastion:
                print("Using Bastion, testing SSH tunnel...")
                self.tunnel = SSHTunnelForwarder(
                    os.getenv("JPC_BASTION_SERVER", default=config["bastion_server"]),
                    ssh_username=os.getenv(
                        "JPC_BASTION_USER", default=config["bastion_user"]
                    ),
                    remote_bind_address=(
                        os.getenv("JPC_BASTION_HOST", default=config["bastion_host"]),
                        REDSHIFT_PORT,
                    ),
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

    def change(self, name, configfile=None):
        "change DB to query against"
        self._get_engine_tunnel(self._load_config_yaml(name, configfile))

    def __init__(self, name=None, configfile=None):
        self.change(name, configfile)

    def close_tunnel(self):
        if self.tunnel:
            self.tunnel.close()

    def connect(self):
        try:
            if self.tunnel:
                self.tunnel.start()

        except HandlerSSHTunnelForwarderError:
            print(f"Tunnel to {REDSHIFT_PORT} already opened, moving on...")

        return self.engine.connect()
