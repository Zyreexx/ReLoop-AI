"""
Tests for Diagnostics Agent Packaging, Health Check, and CLI contracts.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import pytest
from diagnostics_agent.runner import AGENT_VERSION, run_health_check
from diagnostics_agent.os_detect import detect_os

def test_agent_version_constant():
    assert AGENT_VERSION == "1.2.0"
    assert len(AGENT_VERSION.split(".")) == 3

def test_run_health_check_structure():
    health = run_health_check()
    assert isinstance(health, dict)
    assert health["status"] in ["HEALTHY", "DEGRADED", "UNHEALTHY"]
    assert health["version"] == AGENT_VERSION
    assert "checks" in health
    checks = health["checks"]
    assert "os_supported" in checks
    assert "os_system" in checks
    assert "adapter_initialized" in checks
    assert checks["adapter_initialized"] is True

def test_runner_cli_version(monkeypatch):
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{str(root_dir)}{os.pathsep}{env.get('PYTHONPATH', '')}"
    res = subprocess.run(
        [sys.executable, "-m", "diagnostics_agent.runner", "--version"],
        capture_output=True,
        text=True,
        cwd=str(root_dir),
        env=env,
    )
    assert res.returncode == 0
    assert "ReLoop AI Diagnostics Agent v1.2.0" in res.stdout

def test_runner_cli_health(tmp_path):
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{str(root_dir)}{os.pathsep}{env.get('PYTHONPATH', '')}"
    out_file = tmp_path / "health.json"
    res = subprocess.run(
        [sys.executable, "-m", "diagnostics_agent.runner", "--health", "--json-output", str(out_file)],
        capture_output=True,
        text=True,
        cwd=str(root_dir),
        env=env,
    )
    assert res.returncode == 0
    assert out_file.exists()
    with open(out_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["version"] == AGENT_VERSION
    assert data["status"] in ["HEALTHY", "DEGRADED"]
