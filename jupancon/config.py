"""
Jupancon Configuration.

This module handles the engine and SSH tunnels connecting to the
DB of choice.
"""

import os
from collections import defaultdict
from pathlib import Path

import yaml
import redshift_connector as redc
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
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

    def _env(self, name):
        """
        Helper function, get environment variable first, otherwise get it from the YAML file. 
        NOTE: Doesn't work for all variables, but that's fine 
        """
        return os.getenv(f"JPC_{name.upper()}", default=self.config[name])


    def _get_engine_tunnel(self):
        # TODO try/catch this for missing envs
        self.use_bastion = self._env("use_bastion") 
        self.host = LOCALHOST if self.use_bastion else self._env("host") 
        self.port = self.config["port"] if self.config["port"] else REDSHIFT_PORT
        self.dbtype = os.getenv("JPC_DB_TYPE", default=self.config["type"])
        self.user =  self._env("user") or ""
        self.dbname = os.getenv("JPC_DB", default=self.config["dbname"])
        if self.dbtype == "redshift":     
            url = URL.create(
                    drivername='redshift+redshift_connector', 
                    database=self.dbname, 
                    host=self.host,
                    username=self.user,
                    password=self._env('pass') or ""
            )
            args = {"sslmode": "prefer"}
            if self._env("profile"):  
                args_iam = {
                    "iam": True, 
                    "profile": self._env("profile"),
                    "cluster_identifier": self._env("cluster"),
                    "db_user": self._env("dbuser"),
                    "db_groups": self._env("dbgroups"),
                    "auto_create": True,
                }
                args.update(args_iam)

            self.engine = create_engine(url, connect_args=args)

        elif self.dbtype == "bigquery":
            self.project = os.getenv("JPC_GCP_PROJECT", default=self.config["project"])
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
                    self._env("bastion_server"),
                    ssh_username=self._env("bastion_user"),
                    remote_bind_address=(self._env("bastion_host"), REDSHIFT_PORT),
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
        """
        Change the DB to query against
        """
        self.config = self._load_config_yaml(name, configfile)
        self._get_engine_tunnel()


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
