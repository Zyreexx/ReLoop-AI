"""
Operating system detection and diagnostic environment capabilities detection.
Zero third-party dependencies (Python standard library only).
"""
import os
import platform
import shutil
import subprocess
import sys
from typing import Dict, List, Optional


class OSInfo:
    def __init__(
        self,
        system: str,
        release: str,
        version: str,
        machine: str,
        is_admin: bool,
        available_tools: Dict[str, bool],
    ):
        self.system = system  # "Windows", "Darwin", "Linux", or other
        self.release = release
        self.version = version
        self.machine = machine
        self.is_admin = is_admin
        self.available_tools = available_tools

    @property
    def is_windows(self) -> bool:
        return self.system == "Windows"

    @property
    def is_macos(self) -> bool:
        return self.system == "Darwin"

    @property
    def is_linux(self) -> bool:
        return self.system == "Linux"

    def to_dict(self) -> dict:
        return {
            "system": self.system,
            "release": self.release,
            "version": self.version,
            "machine": self.machine,
            "is_admin": self.is_admin,
            "available_tools": self.available_tools,
        }


def check_is_admin() -> bool:
    """Check if the current process has administrator / root privileges."""
    try:
        if platform.system() == "Windows":
            import ctypes
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        else:
            return os.geteuid() == 0
    except Exception:
        return False


def detect_tool(name: str) -> bool:
    """Check if an executable exists on the system PATH."""
    return shutil.which(name) is not None


def detect_os() -> OSInfo:
    """Gather complete host OS information and available diagnostic tooling."""
    system = platform.system()
    release = platform.release()
    version = platform.version()
    machine = platform.machine()
    is_admin = check_is_admin()

    tools_to_check: List[str] = []
    if system == "Windows":
        tools_to_check = [
            "powershell",
            "powershell.exe",
            "pwsh",
            "wmic",
            "powercfg",
            "smartctl",
        ]
    elif system == "Darwin":
        tools_to_check = [
            "system_profiler",
            "ioreg",
            "pmset",
            "diskutil",
            "sysctl",
            "smartctl",
        ]
    elif system == "Linux":
        tools_to_check = [
            "upower",
            "smartctl",
            "sensors",
            "lsblk",
            "lscpu",
            "dmidecode",
            "cat",
        ]

    available_tools = {tool: detect_tool(tool) for tool in tools_to_check}

    return OSInfo(
        system=system,
        release=release,
        version=version,
        machine=machine,
        is_admin=is_admin,
        available_tools=available_tools,
    )
