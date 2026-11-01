"""
Structured Hardware Evidence Collector.
Coordinates platform adapters and executes diagnostics across all 8 subsystems.
Guaranteed read-only execution with zero third-party dependencies.
"""
from datetime import datetime, timezone
import time
from typing import Any, Callable, Dict, List, Optional
from diagnostics_agent.os_detect import OSInfo, detect_os
from diagnostics_agent.adapters.base import BaseDiagnosticAdapter
from diagnostics_agent.adapters.windows import WindowsAdapter
from diagnostics_agent.adapters.macos import MacOSAdapter
from diagnostics_agent.adapters.linux import LinuxAdapter


class StructuredCollector:
    def __init__(self, os_info: Optional[OSInfo] = None):
        self.os_info = os_info or detect_os()
        self.adapter = self._resolve_adapter()

    def _resolve_adapter(self) -> BaseDiagnosticAdapter:
        if self.os_info.is_windows:
            return WindowsAdapter(self.os_info)
        elif self.os_info.is_macos:
            return MacOSAdapter(self.os_info)
        elif self.os_info.is_linux:
            return LinuxAdapter(self.os_info)
        else:
            return WindowsAdapter(self.os_info)

    def collect_all(
        self,
        progress_cb: Optional[Callable[[str, str, Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """
        Execute diagnostics across all 8 hardware subsystems with live progress callbacks.
        """
        subsystems_to_test = [
            ("battery", "Battery Diagnostics", self.adapter.diagnose_battery),
            ("ssd", "Storage (SSD/NVMe) Diagnostics", self.adapter.diagnose_storage),
            ("ram", "System Memory (RAM) Diagnostics", self.adapter.diagnose_memory),
            ("thermals", "Thermal Monitoring & Throttling", self.adapter.diagnose_thermals),
            ("cpu", "Processor (CPU) Architecture", self.adapter.diagnose_cpu),
            ("display", "Display Subsystem & Graphics", self.adapter.diagnose_display),
            ("keyboard", "Keyboard HID & Controller", self.adapter.diagnose_keyboard),
            ("chassis", "Chassis Enclosure & Structural Guide", self.adapter.diagnose_chassis),
            ("system", "System Board & Power Rails", self.adapter.diagnose_system_board),
        ]

        results: Dict[str, Any] = {}
        subsystem_statuses: Dict[str, str] = {}
        all_faults: List[Dict[str, Any]] = []

        for key, display_name, func in subsystems_to_test:
            if progress_cb:
                progress_cb(key, "Running", {"name": display_name})

            try:
                sub_res = func()
            except Exception as e:
                sub_res = {
                    "status": "FAILED",
                    "component_status": "UNKNOWN",
                    "fault_severity": "MEDIUM",
                    "faults": [f"Subsystem diagnostic error: {str(e)}"],
                    "evidence": {},
                    "source": "Diagnostic Collector Error Handler",
                    "observations": [f"Error occurred during {display_name}: {str(e)}"],
                    "notes": "Exception caught gracefully.",
                }

            results[key] = sub_res
            status_val = sub_res.get("status", "PASSED")
            subsystem_statuses[key] = status_val

            for fault_msg in sub_res.get("faults", []):
                all_faults.append({
                    "component": key,
                    "severity": sub_res.get("fault_severity", "MEDIUM"),
                    "description": fault_msg,
                })

            if progress_cb:
                progress_cb(key, status_val, sub_res)

        # Compute overall health determination
        comp_statuses = [r.get("component_status", "UNKNOWN") for r in results.values()]
        if "REPLACE" in comp_statuses:
            overall_status = "DEGRADED"
        elif "WEAR" in comp_statuses:
            overall_status = "FAIR"
        elif all(s == "GOOD" for s in comp_statuses):
            overall_status = "GOOD"
        else:
            overall_status = "FAIR"

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "os": self.os_info.to_dict(),
            "overall_status": overall_status,
            "subsystem_statuses": subsystem_statuses,
            "subsystems": results,
            "faults": all_faults,
            "total_faults_count": len(all_faults),
        }
