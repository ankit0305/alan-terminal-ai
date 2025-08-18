#!/usr/bin/env python3
"""
pytest configuration for Alan Terminal Assistant
Handles Mac-specific test setup and fixtures
"""

import os
import platform
import sys

import pytest

from alan_assistant import AlanAssistant

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def alan():
    """Create AlanAssistant instance for testing"""
    return AlanAssistant()

@pytest.fixture(scope="session")
def platform_info():
    """Provide platform information for tests"""
    return {
        "system": platform.system(),
        "platform": platform.platform(),
        "is_mac": platform.system() == "Darwin",
        "is_windows": platform.system() == "Windows",
        "is_unix": platform.system() in ["Darwin", "Linux"],
        "python_version": sys.version,
        "architecture": platform.architecture()[0],
    }


@pytest.fixture
def mac_commands():
    """Provide Mac-specific test commands"""
    if platform.system() == "Darwin":
        return {
            "list_files": "ls -la",
            "show_processes": "ps aux",
            "disk_usage": "df -h",
            "system_info": "uname -a",
            "network_info": "ifconfig",
            "pipe_command": "ls | head -5",
            "redirect_command": 'echo "test" > /tmp/test.txt',
        }

    return {
        "list_files": "ls -la",
        "show_processes": "ps aux",
        "disk_usage": "df -h",
        "system_info": "uname -a",
        "network_info": "ip addr" if platform.system() == "Linux" else "ipconfig",
        "pipe_command": "ls | head -5",
        "redirect_command": 'echo "test" > /tmp/test.txt',
    }



@pytest.fixture
def safe_test_commands():
    """Provide safe commands for testing across platforms"""
    system = platform.system()

    match system:
        case "Darwin":  # Mac
            return ['echo "Hello Mac"', "date", "whoami", "pwd", "ls /tmp", "uname -s"]
        case "Windows":
            return ['echo "Hello Windows"', "date /t", "whoami", "cd", "dir %TEMP%", "ver"]
        case _:  # Linux/Unix fallback
            return ['echo "Hello Unix"', "date", "whoami", "pwd", "ls /tmp", "uname -s"]



@pytest.fixture
def expected_help_content():
    """Expected content in help message, platform-aware"""
    base_content = ["alan", "please", "usage",
                    "example", "copy", "help", "version"]

    # Add platform-specific expectations if needed
    if platform.system() == "Darwin":
        base_content.extend(["terminal", "assistant"])

    return base_content


# Skip tests based on platform if needed
mac_only = pytest.mark.skipif(
    platform.system() != "Darwin", reason="Mac-only test")

windows_only = pytest.mark.skipif(
    platform.system() != "Windows", reason="Windows-only test"
)

unix_only = pytest.mark.skipif(
    platform.system() not in ["Darwin", "Linux"], reason="Unix-only test"
)
