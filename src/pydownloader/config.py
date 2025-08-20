import os
from configparser import ConfigParser
from pathlib import Path
from typing import List, Optional

# Define the names of the config files we'll look for
CONFIG_FILES = ["config.ini", ".pydownloader.ini"]
# Define the required sections and keys for validation
REQUIRED_SECTIONS = {
    "settings": [
        "dest_folder",
        "connections",
        "max_download_speed",
        "rpc_port"
    ],
    "schedules": [],
}


def find_config_file(search_paths: List[Path]) -> Optional[Path]:
    """
    Searches for a valid config file in a list of paths.

    Args:
        search_paths: A list of directories to search in.

    Returns:
        The path to the first config file found, or None if not found.
    """
    for path in search_paths:
        for config_file in CONFIG_FILES:
            file_path = path / config_file
            if file_path.is_file():
                return file_path
    return None

def validate_config(config: ConfigParser):
    """
    Validates that the config has all the required sections and keys.

    Args:
        config: The ConfigParser object to validate.

    Raises:
        ValueError: If a required section or key is missing.
    """
    for section, keys in REQUIRED_SECTIONS.items():
        if not config.has_section(section):
            raise ValueError(f"Missing required section: '{section}'")
        for key in keys:
            if not config.has_option(section, key):
                raise ValueError(f"Missing required key '{key}' in section '{section}'")

def load_config(search_paths: Optional[List[Path]] = None) -> ConfigParser:
    """
    Loads and validates the application configuration.

    It searches for `config.ini` or `.pydownloader.ini` in the provided
    search paths. If no paths are provided, it defaults to the user's
    home directory and the current working directory.

    Args:
        search_paths: A list of directories to search for the config file.

    Returns:
        A validated ConfigParser object.

    Raises:
        FileNotFoundError: If no configuration file can be found.
        ValueError: If the configuration is invalid (missing sections/keys).
    """
    if search_paths is None:
        # Default search paths: user's home and current directory
        search_paths = [Path.home(), Path.cwd()]

    config_file_path = find_config_file(search_paths)

    if not config_file_path:
        raise FileNotFoundError("Could not find a valid configuration file.")

    config = ConfigParser()
    config.read(config_file_path)

    validate_config(config)

    return config