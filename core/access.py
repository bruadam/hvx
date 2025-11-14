"""
Access Control Models

User profiles, ACL entries, and helper context objects for enforcing access.
"""

from __future__ import annotations
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .enums import PermissionScope, UserRole


class UserProfile(BaseModel):
    """Represents a user or service principal interacting with the twin."""

    id: str
    email: str
    roles: List[UserRole] = Field(default_factory=list)
    organization_id: Optional[str] = None

    display_name: Optional[str] = None
    metadata: Dict[str, str] = Field(default_factory=dict)


class AccessControlEntry(BaseModel):
    """
    Grants permissions on a resource to a principal (user or group).
    """

    principal_id: str
    resource_type: str
    resource_id: str

    scope: PermissionScope
    inherited: bool = False
    metadata: Dict[str, str] = Field(default_factory=dict)


class ResourceReference(BaseModel):
    """Lightweight pointer to any resource with optional ACL metadata."""

    resource_type: str
    resource_id: str
    access_scopes: List[PermissionScope] = Field(default_factory=list)


class UserContext(BaseModel):
    """
    Runtime context carrying the user profile and effective permissions.

    Provides helper methods for access checks inside entity operations.
    """

    user: UserProfile
    permissions: List[AccessControlEntry] = Field(default_factory=list)

    def has_access(self, resource_id: str, scope: PermissionScope) -> bool:
        """
        Check if the user has at least the requested scope on the resource.
        """
        for entry in self.permissions:
            if entry.resource_id == resource_id and entry.scope in (scope, PermissionScope.ADMIN):
                return True
        # admins implicitly have access to everything
        if UserRole.ADMIN in self.user.roles:
            return True
        return False


__all__ = [
    "UserProfile",
    "AccessControlEntry",
    "ResourceReference",
    "UserContext",
]
