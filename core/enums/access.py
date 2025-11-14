"""
User and permission enums.
"""

from enum import Enum


class PermissionScope(str, Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    SHARE = "share"
    ADMIN = "admin"


class UserRole(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"
    OPERATOR = "operator"
    TENANT = "tenant"
    SERVICE = "service"


__all__ = [
    "PermissionScope",
    "UserRole",
]
