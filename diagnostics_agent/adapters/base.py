"""
Base Diagnostic Adapter defining interface for cross-platform hardware telemetry extraction.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from diagnostics_agent.os_detect import OSInfo


class BaseDiagnosticAdapter(ABC):
    def __init__(self, os_info: OSInfo):
        self.os_info = os_info

    @abstractmethod
    def diagnose_battery(self) -> Dict[str, Any]:
        """
        Extract battery design capacity, full charge capacity, cycle count,
        temperature, charging state, and calculate health percentage deterministically.
        """
        pass

    @abstractmethod
    def diagnose_storage(self) -> Dict[str, Any]:
        """
        Extract drive models, capacities, SMART health status, wear percentage,
        reallocated / pending sectors, and temperature.
        """
        pass

    @abstractmethod
    def diagnose_memory(self) -> Dict[str, Any]:
        """
        Extract installed RAM capacity, slot population, speed, and query OS/WHEA
        for uncorrectable or logged memory faults.
        """
        pass

    @abstractmethod
    def diagnose_thermals(self) -> Dict[str, Any]:
        """
        Extract CPU/GPU temperatures, fan status, and detect thermal throttling events.
        """
        pass

    @abstractmethod
    def diagnose_cpu(self) -> Dict[str, Any]:
        """
        Extract CPU model, cores, logical processors, base frequency, and machine check faults.
        """
        pass

    @abstractmethod
    def diagnose_display(self) -> Dict[str, Any]:
        """
        Extract display resolution, refresh rate, internal display connection state,
        graphics adapter, and GPU driver status.
        """
        pass

    @abstractmethod
    def diagnose_keyboard(self) -> Dict[str, Any]:
        """
        Extract internal keyboard HID device status and driver operational health.
        """
        pass

    @abstractmethod
    def diagnose_chassis(self) -> Dict[str, Any]:
        """
        Extract enclosure form factor and guide physical inspection of hinges/casing.
        """
        pass

    @abstractmethod
    def diagnose_system_board(self) -> Dict[str, Any]:
        """
        Extract motherboard vendor, model, BIOS/UEFI version, PCIe/USB bus controller status,
        and query hardware error logs (WHEA / MCE).
        """
        pass

    def _default_unknown(self, component: str, reason: str) -> Dict[str, Any]:
        return {
            "status": "UNSUPPORTED",
            "component_status": "UNKNOWN",
            "fault_severity": "INFO",
            "faults": [],
            "evidence": {},
            "source": "OS Hardware Telemetry",
            "observations": [f"Insufficient evidence: {reason}"],
            "notes": "Telemetric data could not be collected safely or is not exposed by hardware.",
        }
