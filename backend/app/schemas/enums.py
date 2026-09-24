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

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            val_upper = value.upper()
            if val_upper in ["SERVICE_REQUIRED", "FAIR"]:
                return cls.WEAR
            if val_upper in ["REPLACE_REQUIRED"]:
                return cls.REPLACE
        return None


# Backward-compatible attribute references
ComponentStatus.SERVICE_REQUIRED = ComponentStatus.WEAR
ComponentStatus.REPLACE_REQUIRED = ComponentStatus.REPLACE
ComponentStatus.FAIR = ComponentStatus.WEAR


class PathwayType(str, Enum):
    REPAIR = "REPAIR"
    UPGRADE = "UPGRADE"
    REFURBISH = "REFURBISH"
    REUSE = "REUSE"
    COMPONENT_RECOVERY = "COMPONENT_RECOVERY"
    RECYCLE = "RECYCLE"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            val_upper = value.upper()
            if val_upper in ["REUSE_REDEPLOY"]:
                return cls.REUSE
        return None


PathwayType.REUSE_REDEPLOY = PathwayType.REUSE


class Objective(str, Enum):
    LOWEST_COST = "LOWEST_COST"
    MAX_LIFE = "MAX_LIFE"
    ENVIRONMENTAL = "ENVIRONMENTAL"
    FASTEST_RECOVERY = "FASTEST_RECOVERY"

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


Objective.MAXIMUM_LIFE = Objective.MAX_LIFE
Objective.ENVIRONMENTAL_BENEFIT = Objective.ENVIRONMENTAL

# Compatibility alias for code referencing ObjectiveType
ObjectiveType = Objective


class DeviceCategory(str, Enum):
    LAPTOP = "LAPTOP"


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
