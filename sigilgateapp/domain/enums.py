from enum import Enum


class Status(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class NodeRole(str, Enum):
    CORE = "core"
    ENTRY = "entry"
    MGMT = "mgmt"
