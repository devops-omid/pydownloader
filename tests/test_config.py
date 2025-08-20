import pytest
from configparser import ConfigParser
from pydownloader import config

# A sample valid configuration for our tests
VALID_CONFIG_CONTENT = """
[settings]
dest_folder = /downloads
connections = 8
max_download_speed = 10M
rpc_port = 6800

[schedules]
s1 = 09:00-17:00-2M
"""

def test_load_valid_config(tmp_path):
    """
    Tests that a valid config.ini file is parsed correctly.
    """
    # Create a temporary config file
    config_file = tmp_path / "config.ini"
    config_file.write_text(VALID_CONFIG_CONTENT)

    # We expect a function `load_config` to exist and return a ConfigParser object
    # We pass the directory of the temp file as the search path
    cfg = config.load_config(search_paths=[tmp_path])

    assert isinstance(cfg, ConfigParser)
    assert cfg.get("settings", "dest_folder") == "/downloads"
    assert cfg.getint("settings", "connections") == 8
    assert cfg.get("schedules", "s1") == "09:00-17:00-2M"

def test_config_not_found():
    """
    Tests that FileNotFoundError is raised if no config file is found.
    """
    # We expect the function to raise an error if we give it an empty directory
    with pytest.raises(FileNotFoundError):
        config.load_config(search_paths=[])

def test_missing_section(tmp_path):
    """
    Tests that a ValueError is raised if a required section is missing.
    """
    # Create a config file that's missing the [settings] section
    invalid_content = "[schedules]\ns1 = 09:00-17:00-2M"
    config_file = tmp_path / "config.ini"
    config_file.write_text(invalid_content)

    with pytest.raises(ValueError, match="Missing required section: 'settings'"):
        config.load_config(search_paths=[tmp_path])

def test_missing_key(tmp_path):
    """
    Tests that a ValueError is raised if a required key is missing.
    """
    # Create a config file that's missing the 'dest_folder' key
    invalid_content = "[settings]\nconnections = 8"
    config_file = tmp_path / "config.ini"
    config_file.write_text(invalid_content)

    with pytest.raises(ValueError, match="Missing required key 'dest_folder' in section 'settings'"):
        config.load_config(search_paths=[tmp_path])

def test_missing_rpc_port(tmp_path):
    """
    Tests that a ValueError is raised if 'rpc_port' is missing.
    """
    # Config content missing the rpc_port
    invalid_content = """
    [settings]
    dest_folder = /downloads
    connections = 8
    max_download_speed = 10M
    """
    config_file = tmp_path / "config.ini"
    config_file.write_text(invalid_content)

    with pytest.raises(ValueError, match="Missing required key 'rpc_port' in section 'settings'"):
        config.load_config(search_paths=[tmp_path])

