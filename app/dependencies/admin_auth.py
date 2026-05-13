"""
Admin Authentication Dependencies

This module provides FastAPI dependencies for admin authentication and authorization.
It handles:
- Token validation
- Permission checking
- Role verification
"""

from typing import List, Optional
from fastapi import HTTPException, Depends, status, Request
from sqlalchemy.orm import Session
from functools import wraps

from app.core.database import get_db
from app.model.admin_table import AdminTable, AdminRole, ROLE_PERMISSIONS, AdminPermissions
from app.model.admin_session_table import AdminSessionTable
from app.utils.token import Token
from app.utils.hashing import Hashing


class AdminAuth:
    """Admin authentication and authorization class"""
    
    def __init__(self):
        self.token_service = Token()

    def _get_role_permissions(self, admin: AdminTable) -> List[str]:
        return ROLE_PERMISSIONS.get(AdminRole(admin.role), [])
    
    def get_current_admin(self, request: Request, db: Session = Depends(get_db)):
        """
        Dependency to get the current authenticated admin from the request.
        
        Args:
            request: The FastAPI request object
            db: Database session
            
        Returns: AdminTable object with additional 'permissions' attribute
        """
        try:
            # Get authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing or invalid authorization header"
                )
            
            token = auth_header.replace("Bearer ", "")
            
            # Decode token
            payload = self.token_service.decode_token(token)
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token"
                )
            
            # Check token type
            if payload.get("type") != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            admin_id = payload.get("admin_id")
            if not admin_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            # Get admin from database
            admin = db.query(AdminTable).filter(AdminTable.admin_id == admin_id).first()
            if not admin:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Admin not found"
                )
            
            if not admin.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin account is inactive"
                )
            
            # Verify a still-active session matches this exact access token.
            sessions = db.query(AdminSessionTable).filter(
                AdminSessionTable.admin_id == admin_id,
                AdminSessionTable.is_login == True,
                AdminSessionTable.access_token_hash.isnot(None)
            ).all()
            
            if not sessions:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session not found or expired"
                )
            
            if not any(Hashing.verify_hash(token, session.access_token_hash) for session in sessions):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            
            # Keep computed role permissions off the mapped permissions column.
            admin.role_permissions = self._get_role_permissions(admin)
            admin.token_payload = payload
            
            return admin
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"Admin auth error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication error"
            )
    
    def require_permission(self, required_permission: str):
        """
        Dependency factory to require a specific permission.
        
        Args:
            required_permission: The permission string required
            
        Returns:
            Dependency function that checks for the permission
        """
        async def permission_dependency(request: Request, db: Session = Depends(get_db)):
            current_admin = self.get_current_admin(request, db)
            if required_permission not in current_admin.role_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {required_permission} required"
                )
            return current_admin
        
        return permission_dependency
    
    def require_any_permission(self, permissions: List[str]):
        """
        Dependency factory to require any of the specified permissions.
        
        Args:
            permissions: List of permission strings (any one is sufficient)
            
        Returns:
            Dependency function that checks for any permission
        """
        async def any_permission_dependency(request: Request, db: Session = Depends(get_db)):
            current_admin = self.get_current_admin(request, db)
            if not any(perm in current_admin.role_permissions for perm in permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: one of {permissions} required"
                )
            return current_admin
        
        return any_permission_dependency
    
    def require_all_permissions(self, permissions: List[str]):
        """
        Dependency factory to require all of the specified permissions.
        
        Args:
            permissions: List of permission strings (all are required)
            
        Returns:
            Dependency function that checks for all permissions
        """
        async def all_permissions_dependency(request: Request, db: Session = Depends(get_db)):
            current_admin = self.get_current_admin(request, db)
            if not all(perm in current_admin.role_permissions for perm in permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: all of {permissions} required"
                )
            return current_admin
        
        return all_permissions_dependency
    
    def require_role(self, required_role: AdminRole):
        """
        Dependency factory to require a specific role.
        
        Args:
            required_role: The AdminRole required
            
        Returns:
            Dependency function that checks for the role
        """
        async def role_dependency(request: Request, db: Session = Depends(get_db)):
            current_admin = self.get_current_admin(request, db)
            role_hierarchy = {
                AdminRole.VIEWER: 1,
                AdminRole.MODERATOR: 2,
                AdminRole.SUPER_ADMIN: 3
            }
            
            admin_role = AdminRole(current_admin.role)
            if role_hierarchy.get(admin_role, 0) < role_hierarchy.get(required_role, 0):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role denied: {required_role.value} or higher required"
                )
            return current_admin
        
        return role_dependency
    
    def require_super_admin(self):
        """
        Dependency factory to require super_admin role.
        
        Returns:
            Dependency function that checks for super_admin role
        """
        return self.require_role(AdminRole.SUPER_ADMIN)
    
    def require_moderator_or_higher(self):
        """
        Dependency factory to require moderator or super_admin role.
        
        Returns:
            Dependency function that checks for moderator+ role
        """
        async def moderator_dependency(request: Request, db: Session = Depends(get_db)):
            current_admin = await self.get_current_admin(request, db)
            admin_role = AdminRole(current_admin.role)
            if admin_role not in [AdminRole.MODERATOR, AdminRole.SUPER_ADMIN]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Moderator or super admin role required"
                )
            return current_admin
        
        return moderator_dependency


# Create global instance
admin_auth = AdminAuth()

# Convenience dependencies - these are factory functions that return async dependencies
get_current_admin = admin_auth.get_current_admin
require_permission = admin_auth.require_permission
require_any_permission = admin_auth.require_any_permission
require_all_permissions = admin_auth.require_all_permissions
require_role = admin_auth.require_role
require_super_admin = admin_auth.require_super_admin
require_moderator_or_higher = admin_auth.require_moderator_or_higher
