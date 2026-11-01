"""
Unit tests for ReLoop AI Cross-Platform Smart Diagnostics Agent.
"""
try:
    import pytest
except ImportError:
    class _MockPytest:
        @staticmethod
        def fixture(func):
            return func
    pytest = _MockPytest()  # type: ignore
from unittest.mock import MagicMock, patch
from diagnostics_agent.os_detect import OSInfo, detect_os
from diagnostics_agent.adapters.base import BaseDiagnosticAdapter
from diagnostics_agent.adapters.windows import WindowsAdapter
from diagnostics_agent.adapters.macos import MacOSAdapter
from diagnostics_agent.adapters.linux import LinuxAdapter
from diagnostics_agent.collector import StructuredCollector


@pytest.fixture
def win_os_info():
    return OSInfo(
        system="Windows",
        release="11",
        version="10.0.22631",
        machine="AMD64",
        is_admin=False,
        available_tools={"powershell": True, "powercfg": True},
    )


@pytest.fixture
def mac_os_info():
    return OSInfo(
        system="Darwin",
        release="23.4.0",
        version="Darwin Kernel Version 23.4.0",
        machine="arm64",
        is_admin=False,
        available_tools={"system_profiler": True, "ioreg": True, "pmset": True},
    )


@pytest.fixture
def linux_os_info():
    return OSInfo(
        system="Linux",
        release="6.5.0-generic",
        version="#1 SMP",
        machine="x86_64",
        is_admin=False,
        available_tools={"upower": True, "smartctl": True, "sensors": True},
    )


# --- OS Detection Tests ---
def test_os_info_properties(win_os_info, mac_os_info, linux_os_info):
    assert win_os_info.is_windows is True
    assert win_os_info.is_macos is False
    assert win_os_info.is_linux is False

    assert mac_os_info.is_macos is True
    assert mac_os_info.is_windows is False

    assert linux_os_info.is_linux is True
    assert linux_os_info.is_windows is False


def test_detect_os_live():
    info = detect_os()
    assert info.system in ["Windows", "Darwin", "Linux"]
    assert isinstance(info.is_admin, bool)
    assert isinstance(info.available_tools, dict)


# --- Windows Adapter Tests ---
def test_windows_battery_thresholds(win_os_info):
    adapter = WindowsAdapter(win_os_info)

    # 1. Healthy Battery (85% health, 200 cycles -> GOOD)
    with patch.object(adapter, "_run_ps_json") as mock_ps:
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", MagicMock(return_value=MagicMock(
                __enter__=lambda s: MagicMock(read=lambda: "<DesignCapacity>50000</DesignCapacity><FullChargeCapacity>42500</FullChargeCapacity><CycleCount>200</CycleCount>"),
                __exit__=lambda s, e, v, t: None,
            ))):
                res = adapter.diagnose_battery()
                assert res["status"] == "PASSED"
                assert res["component_status"] == "GOOD"
                assert res["evidence"]["health_percentage"] == 85.0
                assert res["fault_severity"] == "INFO"

    # 2. Degraded Battery (40% health -> REPLACE)
    with patch.object(adapter, "_run_ps_json") as mock_ps:
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", MagicMock(return_value=MagicMock(
                __enter__=lambda s: MagicMock(read=lambda: "<DesignCapacity>50000</DesignCapacity><FullChargeCapacity>20000</FullChargeCapacity><CycleCount>350</CycleCount>"),
                __exit__=lambda s, e, v, t: None,
            ))):
                res = adapter.diagnose_battery()
                assert res["status"] == "FAULT_DETECTED"
                assert res["component_status"] == "REPLACE"
                assert res["evidence"]["health_percentage"] == 40.0
                assert res["fault_severity"] == "HIGH"
                assert any("Severe battery degradation" in f for f in res["faults"])

    # 3. High Cycles Battery (85% health, 650 cycles -> WEAR)
    with patch.object(adapter, "_run_ps_json") as mock_ps:
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", MagicMock(return_value=MagicMock(
                __enter__=lambda s: MagicMock(read=lambda: "<DesignCapacity>50000</DesignCapacity><FullChargeCapacity>42500</FullChargeCapacity><CycleCount>650</CycleCount>"),
                __exit__=lambda s, e, v, t: None,
            ))):
                res = adapter.diagnose_battery()
                assert res["status"] == "FAULT_DETECTED"
                assert res["component_status"] == "WEAR"
                assert any("Elevated cycle count" in f for f in res["faults"])


def test_windows_storage_smart_evaluation(win_os_info):
    adapter = WindowsAdapter(win_os_info)

    # 1. Healthy NVMe SSD
    with patch.object(adapter, "_run_ps_json") as mock_ps:
        mock_ps.side_effect = [
            {"DeviceId": "0", "FriendlyName": "NVMe SSD 512GB", "MediaType": "SSD", "OperationalStatus": "OK", "HealthStatus": "Healthy", "Size": 512000000000},
            {"PredictFailure": False},
        ]
        res = adapter.diagnose_storage()
        assert res["status"] == "PASSED"
        assert res["component_status"] == "GOOD"
        assert res["evidence"]["smart_status"] == "PASS"

    # 2. Failing SSD
    with patch.object(adapter, "_run_ps_json") as mock_ps:
        mock_ps.side_effect = [
            {"DeviceId": "0", "FriendlyName": "Faulty SSD", "MediaType": "SSD", "OperationalStatus": "Degraded", "HealthStatus": "Unhealthy", "Size": 512000000000},
            {"PredictFailure": True},
        ]
        res = adapter.diagnose_storage()
        assert res["status"] == "FAULT_DETECTED"
        assert res["component_status"] == "REPLACE"
        assert res["evidence"]["smart_status"] == "FAIL"
        assert res["fault_severity"] == "CRITICAL"


def test_windows_memory_evaluation(win_os_info):
    adapter = WindowsAdapter(win_os_info)

    # Clean memory modules
    with patch.object(adapter, "_run_ps_json") as mock_ps:
        mock_ps.side_effect = [
            [{"Capacity": 8589934592, "Speed": 3200, "DeviceLocator": "DIMM 0"}, {"Capacity": 8589934592, "Speed": 3200, "DeviceLocator": "DIMM 1"}],
            {"MemoryDevices": 2},
            None,  # No WHEA errors
        ]
        res = adapter.diagnose_memory()
        assert res["status"] == "PASSED"
        assert res["component_status"] == "GOOD"
        assert res["evidence"]["installed_gb"] == 16
        assert res["evidence"]["slots_used"] == 2


def test_windows_thermals_throttling(win_os_info):
    adapter = WindowsAdapter(win_os_info)

    # Throttling detected
    with patch.object(adapter, "_run_ps_json") as mock_ps:
        mock_ps.side_effect = [
            [{"TimeCreated": "2026-03-01T12:00:00", "Message": "Speed limited by firmware"}],
            {"CurrentTemperature": 3682},  # 95°C
        ]
        res = adapter.diagnose_thermals()
        assert res["status"] == "FAULT_DETECTED"
        assert res["component_status"] == "WEAR"
        assert res["evidence"]["throttling_detected"] is True
        assert res["evidence"]["service_recommended"] is True


def test_windows_system_board_evaluation(win_os_info):
    adapter = WindowsAdapter(win_os_info)

    # Healthy motherboard
    with patch.object(adapter, "_run_ps_json") as mock_ps:
        mock_ps.side_effect = [
            {"Manufacturer": "Dell Inc.", "Product": "0K3X20", "Status": "OK"},
            {"SMBIOSBIOSVersion": "1.14.0"},
            None,  # No critical WHEA errors
        ]
        res = adapter.diagnose_system_board()
        assert res["status"] == "PASSED"
        assert res["component_status"] == "GOOD"
        assert res["evidence"]["post_successful"] is True


# --- macOS Adapter Tests ---
def test_macos_battery_evaluation(mac_os_info):
    adapter = MacOSAdapter(mac_os_info)
    with patch.object(adapter, "_run_system_profiler") as mock_sp:
        mock_sp.return_value = {
            "SPPowerDataType": [{
                "sppower_battery_health_info": {
                    "sppower_battery_cycle_count": 180,
                    "sppower_battery_health": "Normal",
                    "sppower_battery_max_capacity": "91%",
                }
            }]
        }
        res = adapter.diagnose_battery()
        assert res["status"] == "PASSED"
        assert res["component_status"] == "GOOD"
        assert res["evidence"]["health_percentage"] == 91.0


def test_macos_storage_evaluation(mac_os_info):
    adapter = MacOSAdapter(mac_os_info)
    with patch.object(adapter, "_run_system_profiler") as mock_sp:
        mock_sp.return_value = {
            "SPStorageDataType": [{
                "_name": "APPLE SSD AP0512Q",
                "smart_status": "Verified",
                "size_in_bytes": 500000000000,
            }]
        }
        res = adapter.diagnose_storage()
        assert res["status"] == "PASSED"
        assert res["component_status"] == "GOOD"
        assert res["evidence"]["smart_status"] == "PASS"


# --- Linux Adapter Tests ---
def test_linux_battery_evaluation(linux_os_info):
    adapter = LinuxAdapter(linux_os_info)
    with patch("glob.glob", return_value=["/sys/class/power_supply/BAT0"]):
        with patch.object(adapter, "_read_file") as mock_rf:
            def read_side_effect(path):
                if "energy_full_design" in path:
                    return "50000000"  # 50000 mWh
                elif "energy_full" in path:
                    return "45000000"  # 45000 mWh (90%)
                elif "cycle_count" in path:
                    return "120"
                return None
            mock_rf.side_effect = read_side_effect
            res = adapter.diagnose_battery()
            assert res["status"] == "PASSED"
            assert res["component_status"] == "GOOD"
            assert res["evidence"]["health_percentage"] == 90.0
            assert res["evidence"]["cycle_count"] == 120


# --- Collector Integration Tests ---
def test_structured_collector_all_subsystems(win_os_info):
    collector = StructuredCollector(win_os_info)

    # Mock all adapter methods
    collector.adapter.diagnose_battery = MagicMock(return_value={"status": "PASSED", "component_status": "GOOD", "faults": [], "evidence": {"health_percentage": 92.0}})
    collector.adapter.diagnose_storage = MagicMock(return_value={"status": "PASSED", "component_status": "GOOD", "faults": [], "evidence": {"smart_status": "PASS"}})
    collector.adapter.diagnose_memory = MagicMock(return_value={"status": "PASSED", "component_status": "GOOD", "faults": [], "evidence": {"installed_gb": 16}})
    collector.adapter.diagnose_thermals = MagicMock(return_value={"status": "PASSED", "component_status": "GOOD", "faults": [], "evidence": {"throttling_detected": False}})
    collector.adapter.diagnose_cpu = MagicMock(return_value={"status": "PASSED", "component_status": "GOOD", "faults": [], "evidence": {"cores": 8}})
    collector.adapter.diagnose_display = MagicMock(return_value={"status": "PASSED", "component_status": "GOOD", "faults": [], "evidence": {"resolution": "1920x1080"}})
    collector.adapter.diagnose_keyboard = MagicMock(return_value={"status": "PASSED", "component_status": "GOOD", "faults": [], "evidence": {"status": "OK"}})
    collector.adapter.diagnose_chassis = MagicMock(return_value={"status": "PASSED", "component_status": "GOOD", "faults": [], "evidence": {"form_factor": "Laptop"}})
    collector.adapter.diagnose_system_board = MagicMock(return_value={"status": "PASSED", "component_status": "GOOD", "faults": [], "evidence": {"post_successful": True}})

    report = collector.collect_all()
    assert report["overall_status"] == "GOOD"
    assert report["total_faults_count"] == 0
    assert len(report["subsystems"]) == 9
    assert report["subsystems"]["battery"]["evidence"]["health_percentage"] == 92.0
