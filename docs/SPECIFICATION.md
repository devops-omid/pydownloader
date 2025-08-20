# Project Specification: PyDownloader

## 1. Overview

PyDownloader is a command-line application written in Python that acts as a sophisticated controller for the `aria2c` download utility. It manages `aria2c` as a persistent background daemon, enabling advanced features like bandwidth scheduling, download queuing, and status monitoring. The application is designed to be robust, easy to use, and highly configurable.

---

## 2. Core Features

* **Daemon Management**: Start, stop, and check the status of the `aria2c` background process.
* **Download Queuing**: Add single URLs or a list of URLs from a text file to the download queue without interrupting the daemon.
* **Advanced Bandwidth Scheduling**:
    * Define multiple, prioritized time slots with different speed limits (e.g., "2M" during work hours, "10M" at night).
    * A default maximum speed is used for any time outside of a defined schedule.
    * The speed limit of in-progress downloads is updated automatically and on the fly as schedule changes occur.
* **Status Monitoring**:
    * View a list of all downloads (active, waiting, completed, and failed) in a clearly formatted table.
    * Display the status of each download using clear, intuitive icons:
        * `⏳` (Active/Waiting)
        * `⏸️` (Paused)
        * `✅` (Completed Successfully)
        * `❌` (Failed/Error)
* **Queue Management**:
    * **Remove**: Remove a specific download (active, waiting, or paused) from the queue.
    * **Reorder**: Change the priority of downloads by moving them up or down in the queue.
* **Secure Configuration**: All settings, including credentials and schedules, are managed in a simple `.ini` configuration file.
* **Logging**: Maintain a log file of all major events, including downloads started, finished, failed, and any application errors.

---

## 3. Technologies & Frameworks

* **Language**: Python 3.9+
* **Backend**: `aria2c` (must be installed on the system and available in the PATH).
* **CLI Framework**: **Typer** or **Click**. These provide a robust and user-friendly way to build the command-line interface with automatic help generation.
* **Table Formatting**: **Rich** or **tabulate**. These libraries make it easy to create well-formatted console tables.
* **Configuration Parsing**: Python's built-in `configparser` library.
* **aria2c Integration**: **aria2p** library. This provides a clean Pythonic wrapper around the `aria2c` RPC interface, simplifying communication with the daemon.
* **Testing Framework**: **pytest**.
* **Mocking Library**: Python's built-in `unittest.mock`.

---

## 4. Architecture

The application follows a **Controller-Daemon** model.

1.  **The Daemon**: An `aria2c` process is launched in the background with its RPC server enabled. This process is long-lived and handles all the actual downloading.
2.  **The Controller (`downloader.py`)**: This is the Python script the user interacts with. It does not download anything itself. Instead, it translates user commands (like `add`, `stop`, `list`) into RPC calls that are sent to the `aria2c` daemon.
3.  **The Scheduler (`scheduler.py`)**: This script is designed to be run by a system scheduler (like `cron`). It reads the configuration, determines the correct speed limit for the current time, and sends an RPC call to the daemon to update its settings.

---

## 5. Project Structure

The project will use the `src` layout to ensure a clean separation between source code and project management files.

```
pydownloader/
├── .github/              # CI/CD workflows (e.g., GitHub Actions)
│   └── workflows/
│       └── python-app.yml
├── docs/
│   └── SPECIFICATION.md
├── src/
│   └── pydownloader/     # Main application package
│       ├── __init__.py
│       ├── __main__.py   # Entry point for `python -m pydownloader`
│       ├── cli.py        # Command-line interface logic (Typer/Click)
│       ├── config.py     # Configuration handling
│       ├── daemon.py     # Daemon management logic
│       ├── scheduler.py  # Scheduling logic
│       └── utils.py      # Utility functions
├── tests/                # Unit and integration tests
│   ├── __init__.py
│   └── test_scheduler.py
├── .gitignore
├── pyproject.toml        # Project metadata and dependencies (PEP 621)
├── README.md
└── config.ini.example    # An example configuration file for users
```

### Module Descriptions

* **`src/pydownloader/__init__.py`**: Marks the `pydownloader` directory as a Python package. Can be left empty.

* **`src/pydownloader/__main__.py`**: Provides the main entry point for the application when invoked with `python -m pydownloader`. Its primary role is to import the main function from `cli.py` and execute it. This allows the package to be run as a script.

* **`src/pydownloader/config.py`**:
    * **Responsibility**: Handles all interactions with the configuration file.
    * **Implementation**: It will use the built-in `configparser` library. It must contain a function that searches for the config file in a prioritized list of locations: first in the user's home directory (e.g., `~/.pydownloader.ini`), and then in the project's root directory (`config.ini`). The first file found will be used. It will parse the `[settings]` and `[schedules]` sections, providing a clean, validated data structure for other modules to use. It must gracefully handle missing files, sections, or keys with sensible defaults.

* **`src/pydownloader/daemon.py`**:
    * **Responsibility**: Manages the lifecycle of the `aria2c` background process.
    * **Implementation**: This module will use the `subprocess` module to start `aria2c` as a detached daemon process. It will construct the `aria2c` command with all necessary RPC options (`--enable-rpc`, `--rpc-listen-port`, `--rpc-secret`, etc.) derived from `config.py`. It will manage a PID (Process ID) file to track the daemon's state for `start`, `stop`, and `status` commands. The `stop` function will read the PID and terminate the process.

* **`src/pydownloader/cli.py`**:
    * **Responsibility**: Defines the user-facing command-line interface. It is the primary controller that orchestrates the application's functions based on user input.
    * **Implementation**: This module will be built using the **Typer** (or Click) library. It will define functions for each command (`start`, `stop`, `add`, `list`, `remove`, `move`, `scheduler`). These functions will parse command-line arguments and options. They will then call the appropriate logic from other modules (e.g., `daemon.py` for start/stop, `aria2p` for queue management). For the `list` command, it will use the **Rich** library to format the download information into a clean, readable table.

* **`src/pydownloader/scheduler.py`**:
    * **Responsibility**: Contains the core logic for determining and applying the correct download speed based on the defined schedules.
    * **Implementation**: It will read the schedules from the config module. It will contain a function that gets the current time and iterates through the schedules in order of priority (`s1`, `s2`, ...). It must correctly handle time ranges that span midnight. Once the correct speed is determined, it will use the `aria2p` library to connect to the running daemon and send an RPC call (`aria2.change_global_option({'max-overall-download-limit': '2M'})`) to update the speed limit on the fly.

* **`src/pydownloader/utils.py`**:
    * **Responsibility**: A collection of shared helper functions used by multiple modules to avoid code duplication.
    * **Implementation**: This could include functions for setting up the logger based on the config file, a function to truncate long URLs for the `list` command's display, or functions to format data sizes (e.g., bytes to MB).

---

## 6. Coding Guidelines

* **Style**: All code must adhere strictly to the **PEP 8** style guide. Use tools like `black` and `flake8` to enforce this automatically.
* **Type Hinting**: All function signatures and variables should include type hints as per PEP 484. This improves code clarity and allows for static analysis.
* **Docstrings**: All modules, classes, and functions must have Google-style docstrings explaining their purpose, arguments, and return values.
* **Modularity**: The code should be organized into logical modules as shown in the Project Structure section.
* **Error Handling**: Use `try...except` blocks to gracefully handle potential errors, such as `aria2c` not being installed, the daemon being unreachable, or configuration file issues.

---

## 7. Unit Testing

* **Full Coverage**: The goal is to achieve **100% test coverage** for the Python controller and scheduler logic. The `aria2c` backend itself will not be tested.
* **Mocking**: All interactions with the `aria2c` RPC interface **must** be mocked using `unittest.mock`. Tests should simulate various responses from the daemon (e.g., success, error, different download statuses) to validate the controller's logic.
* **Test Cases**:
    * **Configuration**: Test loading valid configurations, handling missing values, and parsing schedule strings correctly.
    * **Scheduler Logic**: Test the time-checking logic for all cases, including normal day schedules, overnight schedules, and times that fall into the default speed category.
    * **CLI Commands**: Test that each CLI command (`start`, `stop`, `add`, `list`, `remove`, `move`) calls the correct underlying functions with the right parameters.
    * **Status Parsing**: Test the logic that translates `aria2c` status responses into the user-friendly table with the correct icons, percentages, and truncated URLs.
* **CI/CD**: A continuous integration pipeline (e.g., using GitHub Actions) should be set up to automatically run all tests on every push.

---

## 8. Configuration File

The application will be configured via a single `.ini` file. The application will search for this file in the following locations, in order:

1.  **User's Home Directory**: A hidden file named `.pydownloader.ini` in the user's home folder (e.g., `/home/user/.pydownloader.ini`). This is the recommended location for user-specific settings.
2.  **Project Directory**: A file named `config.ini` in the root of the project folder. This is useful for project-specific configurations that can be checked into version control.

The first file found will be used.

### Example (`.pydownloader.ini` or `config.ini`)
```ini
[settings]
# Full path to the destination folder for downloads.
dest_folder = /path/to/downloads

# Credentials for protected websites.
username = your_username
password = 

# Number of parallel connections per download.
connections = 8

# Default speed for times outside of any defined schedule. Use "0" for unlimited.
max_download_speed = 10M

# Full path to the log file. Leave blank to disable.
log_file = /var/log/pydownloader.log

# Host and port for the aria2c RPC server.
rpc_host = localhost
rpc_port = 6800
rpc_secret = your-secret-token

[schedules]
# Define schedules in the format "HH:MM-HH:MM-SPEED".
# The scheduler uses the *first* matching schedule found.
s1 = 09:00-17:00-2M
s2 = 17:00-22:00-8M
s3 = 22:00-06:00-10M
```

---

## 9. Command-Line Interface (CLI)

The main script `downloader.py` will expose the following commands:

* `python downloader.py start`: Starts the `aria2c` daemon in the background.
* `python downloader.py stop`: Stops the `aria2c` daemon.
* `python downloader.py status`: Reports if the daemon is currently running.
* `python downloader.py add <URL>`: Adds a single download URL to the queue.
* `python downloader.py add-list <PATH_TO_TXT_FILE>`: Adds all URLs from a text file to the queue.
* `python downloader.py list`: Displays the current downloads in a formatted table with columns for Row #, Status, %, and URL (truncated from the start).
* `python downloader.py remove <ROW_NUMBER>`: Removes the download at the specified row number from the queue.
* `python downloader.py move <FROM_ROW> <TO_ROW>`: Moves a download to a new position in the queue, shifting others accordingly.
* `python downloader.py scheduler`: (For internal/cron use) Runs the scheduler logic once to update the daemon's speed limit.

---

## 10. Project Documentation

* **README.md**: The project must include a comprehensive `README.md` file.
* **Content**: The README must contain:
    * A clear and concise project description.
    * A complete list of all features.
    * Detailed installation and configuration instructions.
    * A full usage guide with examples for every CLI command.
* **Maintenance**: This file must be kept up-to-date with every change or addition to the project's features and commands.
