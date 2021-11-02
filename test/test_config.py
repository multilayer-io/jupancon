import os
import pytest

from jupancon.config import JPTConfig


config_path = f"{os.path.abspath(os.path.dirname(__file__))}/test_configfile.yml"

def test_jptconfig_default():
    print(config_path)
    config = JPTConfig(configfile=config_path)
    assert config.name == 'totally-real-gcp'
    assert config.dbtype == 'bigquery'
    


def test_change_non_existing():
    with pytest.raises(Exception) as execinfo:
        JPTConfig(configfile=config_path).change("totally-exists")