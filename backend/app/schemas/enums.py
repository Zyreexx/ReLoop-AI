"""
Shared contract domain enumerations for ReLoop AI with seamless alias resolution.
"""
from enum import Enum


class EvidenceType(str, Enum):
    VISUAL = "VISUAL"
    DIAGNOSTIC = "DIAGNOSTIC"
    USER_REPORTED = "USER_REPORTED"
    DATABASE = "DATABASE"
    ESTIMATE = "ESTIMATE"


class ComponentName(str, Enum):
    BATTERY = "BATTERY"
    SSD = "SSD"
    RAM = "RAM"
    THERMALS = "THERMALS"
    DISPLAY = "DISPLAY"
    KEYBOARD = "KEYBOARD"
    HINGE_CHASSIS = "HINGE_CHASSIS"
    SYSTEM = "SYSTEM"


class ComponentStatus(str, Enum):
    GOOD = "GOOD"
    WEAR = "WEAR"
    REPLACE = "REPLACE"
    DAMAGED = "DAMAGED"
    UNKNOWN = "UNKNOWN"

    # Backward-compatible enum member aliases
    SERVICE_REQUIRED = "WEAR"
    REPLACE_REQUIRED = "REPLACE"
    FAIR = "WEAR"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            val_upper = value.upper()
            if val_upper in ["SERVICE_REQUIRED", "FAIR"]:
                return cls.WEAR
            if val_upper in ["REPLACE_REQUIRED"]:
                return cls.REPLACE
        return None


class PathwayType(str, Enum):
    REPAIR = "REPAIR"
    UPGRADE = "UPGRADE"
    REFURBISH = "REFURBISH"
    REUSE = "REUSE"
    COMPONENT_RECOVERY = "COMPONENT_RECOVERY"
    RECYCLE = "RECYCLE"
    REUSE_REDEPLOY = "REUSE"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            val_upper = value.upper()
            if val_upper in ["REUSE_REDEPLOY"]:
                return cls.REUSE
        return None


class Objective(str, Enum):
    LOWEST_COST = "LOWEST_COST"
    MAX_LIFE = "MAX_LIFE"
    ENVIRONMENTAL = "ENVIRONMENTAL"
    FASTEST_RECOVERY = "FASTEST_RECOVERY"

    # Backward-compatible member aliases
    MAXIMUM_LIFE = "MAX_LIFE"
    ENVIRONMENTAL_BENEFIT = "ENVIRONMENTAL"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            val_upper = value.upper()
            if val_upper in ["MAXIMUM_LIFE", "MAXLIFE", "MAX_LIFE"]:
                return cls.MAX_LIFE
            if val_upper in ["ENVIRONMENTAL_BENEFIT", "ENVIRONMENT", "ENVIRONMENTAL"]:
                return cls.ENVIRONMENTAL
            if val_upper in ["LOWEST_COST", "LOWESTCOST"]:
                return cls.LOWEST_COST
            if val_upper in ["FASTEST_RECOVERY", "FASTESTRECOVERY"]:
                return cls.FASTEST_RECOVERY
        return None


# Compatibility alias for code referencing ObjectiveType
ObjectiveType = Objective


class DeviceCategory(str, Enum):
    LAPTOP = "LAPTOP"
    SMARTPHONE = "SMARTPHONE"
    TABLET = "TABLET"
    DESKTOP = "DESKTOP"
    SERVER = "SERVER"
    MONITOR = "MONITOR"
    OTHER = "OTHER"


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class IdentificationStatus(str, Enum):
    IDENTIFIED = "IDENTIFIED"
    UNKNOWN = "UNKNOWN"
    AI_UNAVAILABLE = "AI_UNAVAILABLE"
    INVALID_EVIDENCE = "INVALID_EVIDENCE"
    CONFIRMATION_REQUIRED = "CONFIRMATION_REQUIRED"
    NON_LAPTOP_REJECTED = "NON_LAPTOP_REJECTED"

