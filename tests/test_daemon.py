import os
import subprocess
from unittest.mock import MagicMock, mock_open, patch

import pytest
from configparser import ConfigParser
from pydownloader import daemon

@pytest.fixture
def mock_config():
    """Provides a mock ConfigParser object for tests."""
    config = ConfigParser()
    config.add_section("settings")
    config.set("settings", "dest_folder", "/test/downloads")
    config.set("settings", "rpc_port", "6800")
    config.set("settings", "rpc_secret", "secret_token")
    return config

@patch("subprocess.Popen")
@patch("builtins.open", new_callable=mock_open)
def test_start_daemon_success(mock_file_open, mock_popen, mock_config, tmp_path):
    """
    Tests that the start function constructs the correct aria2c command
    and writes a PID file.
    """
    # Mock the Popen process to have a specific PID
    mock_process = MagicMock()
    mock_process.pid = 12345
    mock_popen.return_value = mock_process

    pid_file_path = tmp_path / "daemon.pid"

    # Call the function we are testing
    daemon.start(mock_config, pid_file_path)

    # Verify that Popen was called with the correct command
    mock_popen.assert_called_once()
    args, _ = mock_popen.call_args
    command = args[0]
    assert "aria2c" in command
    assert "--enable-rpc" in command
    assert "--rpc-listen-port=6800" in command
    assert "--rpc-secret=secret_token" in command
    assert "--dir=/test/downloads" in command
    assert "--daemon=true" in command

    # Verify that the PID file was written to with the correct PID
    mock_file_open.assert_called_once_with(pid_file_path, "w")
    mock_file_open().write.assert_called_once_with("12345")

@patch("os.kill")
@patch("os.remove")
@patch("builtins.open", new_callable=mock_open, read_data="12345")
def test_stop_daemon_success(mock_file_open, mock_os_remove, mock_os_kill, tmp_path):
    """
    Tests that the stop function reads the PID, kills the process,
    and removes the PID file.
    """
    pid_file_path = tmp_path / "daemon.pid"

    daemon.stop(pid_file_path)

    # Verify PID file was opened for reading
    mock_file_open.assert_called_once_with(pid_file_path, "r")
    # Verify the process was killed
    mock_os_kill.assert_called_once_with(12345, 15) # 15 is SIGTERM
    # Verify the PID file was removed
    mock_os_remove.assert_called_once_with(pid_file_path)

def test_stop_daemon_no_pid_file(tmp_path):
    """
    Tests that the stop function does nothing if the PID file doesn't exist.
    """
    # This should run without error
    daemon.stop(tmp_path / "nonexistent.pid")

@patch("os.path.exists", return_value=True)
@patch("psutil.pid_exists", return_value=True)
@patch("builtins.open", new_callable=mock_open, read_data="12345")
def test_get_status_running(mock_file_open, mock_pid_exists, mock_path_exists, tmp_path):
    """
    Tests the status check when the daemon is running.
    """
    pid_file_path = tmp_path / "daemon.pid"
    status, pid = daemon.get_status(pid_file_path)
    assert status == "Running"
    assert pid == 12345

@patch("os.path.exists", return_value=False)
def test_get_status_stopped(mock_path_exists, tmp_path):
    """
    Tests the status check when the daemon is stopped (no PID file).
    """
    pid_file_path = tmp_path / "daemon.pid"
    status, pid = daemon.get_status(pid_file_path)
    assert status == "Stopped"
    assert pid is None

@patch("os.path.exists", return_value=True)
@patch("psutil.pid_exists", return_value=False)
@patch("builtins.open", new_callable=mock_open, read_data="12345")
def test_get_status_stale_pid(mock_file_open, mock_pid_exists, mock_path_exists, tmp_path):
    """
    Tests the status check when the PID file is stale (process is not running).
    """
    pid_file_path = tmp_path / "daemon.pid"
    status, pid = daemon.get_status(pid_file_path)
    assert status == "Stopped (Stale PID)"
    assert pid is None