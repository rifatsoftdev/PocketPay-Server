import os
from fastapi import APIRouter, HTTPException, Depends, Request, Query, BackgroundTasks
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from sqlalchemy import or_, and_, func, desc
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from decimal import Decimal

from app.core.database import get_db

from app.model.admin_table import AdminTable, AdminRole, ROLE_PERMISSIONS, AdminPermissions
from app.model.admin_session_table import AdminSessionTable
from app.model.user_table import UserTable
from app.model.wallet_table import WalletTable
from app.model.transaction_table import TransactionTable
from app.model.settings_table import SettingsTable
from app.model.notification_table import NotificationTable
from app.enums.transactions_enum import TransactionStatus


from admin.schema.admin_schema import *
from app.schema.global_schema import GlobalResponse

from app.dependencies.admin_auth import (
    get_current_admin,
    require_permission,
    require_super_admin,
    require_moderator_or_higher
)

from app.utils.hashing import Hashing
from app.utils.token import Token
from app.utils.generators import Generators
from app.services.notification.noticication_services import NotificationData, NotificationServices
from app.templates import EmailTemplate, PushTemplate, SMSTemplate
from admin.utils.get_current_admin import get_current_admin

from app.constants.colors import AnsiColor




admin_auth_router = APIRouter()





# ==============================================================================
"""
Admin login

request example
post {
    "email": "admin@example.com",
    "password": "password",
    "android_id": "android_id",
    "uuid": "uuid"
}

response example
{
    "success": true,
    "message": "Login successful",
    "data": {
        "admin_id": "admin_id",
        "email": "admin@example.com",
        "full_name": "Admin Name",
        "role": "super_admin",
        "permissions": ["can_view_users", ...],
        "access_token": "access_token",
        "refresh_token": "refresh_token"
    }
}
"""
# ==============================================================================

@admin_auth_router.post("/login", response_model=GlobalResponse)
async def admin_login(
    request: AdminLoginRequest,
    request_info: Request,
    db: Session = Depends(get_db)):
    try:
        email = request.email
        password = request.password
        android_id = request.device_id
        uuid = request.device_uuid

        # Request info
        ip = request_info.client.host

        # Find admin
        admin = db.query(AdminTable).filter(AdminTable.email == email).first()
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")

        if not admin.is_active:
            raise HTTPException(status_code=403, detail="Admin account is inactive")

        # Verify password
        if not Hashing.verify_password(password, admin.password_hash):
            raise HTTPException(status_code=401, detail="Invalid password")

        # Get permissions based on role
        permissions = ROLE_PERMISSIONS.get(AdminRole(admin.role), [])

        session_id = Generators.generate_id("session")
        now = datetime.now(timezone.utc)

        # Current SQLite schema keeps one admin session row per admin_id.
        # Reuse it on repeated login instead of inserting a duplicate admin_id.
        session = db.query(AdminSessionTable).filter(
            AdminSessionTable.admin_id == admin.admin_id
        ).first()

        if session:
            session.session_id = session_id
            session.device_uuid = uuid
            session.device_id = android_id
            session.last_ip_address = ip
            session.is_login = True
            session.login_at = now
            session.logout_at = None
        else:
            session = AdminSessionTable(
                admin_id=admin.admin_id,
                session_id=session_id,
                device_uuid=uuid,
                device_id=android_id,
                last_ip_address=ip,
                is_login=True,
                login_at=now
            )
            db.add(session)

        db.commit()
        db.refresh(session)

        # Generate tokens
        token_service = Token()
        access_token = token_service.create_access_token(data={
            "admin_id": admin.admin_id,
            "email": admin.email,
            "role": admin.role,
            "permissions": permissions,
            "android_id": android_id,
            "uuid": uuid
        })

        refresh_token = token_service.create_refresh_token(data={
            "admin_id": admin.admin_id,
            "email": admin.email,
            "role": admin.role,
            "permissions": permissions,
            "android_id": android_id,
            "uuid": uuid
        })

        # Update session with token hashes
        session.access_token_hash = Hashing.create_hash(access_token)
        session.refresh_token_hash = Hashing.create_hash(refresh_token)
        db.commit()

        # Update last login
        admin.last_login_at = datetime.now(timezone.utc)
        admin.last_ip_address = ip
        db.commit()

        response = JSONResponse(
            content={
                "success": True,
                "message": "Login successful",
                "data": {
                    "admin_id": admin.admin_id,
                    "email": admin.email,
                    "full_name": admin.full_name,
                    "role": admin.role,
                    "permissions": permissions,
                    "access_token": access_token,
                    "refresh_token": refresh_token
                }
            }
        )

        # 🔐 ACCESS TOKEN COOKIE
        response.set_cookie(
            key="admin_access_token",
            value=access_token,
            httponly=False,          # Allow JavaScript access for admin panel
            secure=False,            # HTTPS হলে True
            samesite="lax",
            max_age=60 * 60         # 1 hour
        )

        # 🔁 REFRESH TOKEN COOKIE
        response.set_cookie(
            key="admin_refresh_token",
            value=refresh_token,
            httponly=False,         # Allow JavaScript access for admin panel
            secure=False,
            samesite="lax",
            max_age=60 * 60 * 24 * 7  # 7 days
        )

        return response

    except HTTPException:
        raise
    
    except Exception as e:
        print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")





# ==============================================================================
"""
Admin logout

request example
post {
    "admin_id": "admin_id",
    "access_token": "access_token",
    "android_id": "android_id",
    "uuid": "uuid"
}

response example
{
    "success": true,
    "message": "Logout successful",
    "data": {}
}
"""
# ==============================================================================

@admin_auth_router.post("/logout")
async def admin_logout(
    request: Request,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)):

    # print(current_admin)

    access_token = request.cookies.get("admin_access_token")
    refresh_token = request.cookies.get("admin_refresh_token")

    # 1️⃣ DB session invalidate
    if access_token:
        token_hash = Hashing.create_hash(access_token)

        session = db.query(AdminSessionTable).filter(
            AdminSessionTable.access_token_hash == token_hash
        ).first()

        if session:
            session.logout_at = datetime.now(timezone.utc)
            session.is_login = False
            db.commit()

    # 2️⃣ Response + cookie clear
    response = JSONResponse({
        "success": True,
        "message": "Logged out successfully"
    })

    response.delete_cookie("admin_access_token")
    response.delete_cookie("admin_refresh_token")

    return response





# ==============================================================================
"""
Refresh access token

request example
post {
    "refresh_token": "refresh_token",
    "android_id": "android_id",
    "uuid": "uuid"
}

response example
{
    "success": true,
    "message": "Token refreshed successfully",
    "data": {
        "access_token": "new_access_token",
        "refresh_token": "new_refresh_token"
    }
}
"""
# ==============================================================================

@admin_auth_router.post("/refresh", response_model=GlobalResponse)
async def refresh_admin_token(
    request: AdminRefreshTokenRequest,
    request_info: Request,
    db: Session = Depends(get_db)):
    try:
        refresh_token = request.refresh_token
        android_id = request.android_id
        uuid = request.uuid

        if not refresh_token:
            raise HTTPException(status_code=400, detail="Refresh token is required")

        # Decode the refresh token
        token_service = Token()
        payload = token_service.decode_token(refresh_token)
        
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        # Check token type
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        admin_id = payload.get("admin_id")
        if not admin_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        # Find admin
        admin = db.query(AdminTable).filter(AdminTable.admin_id == admin_id).first()
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")

        if not admin.is_active:
            raise HTTPException(status_code=403, detail="Admin account is inactive")

        # Verify refresh token hash against session
        session = db.query(AdminSessionTable).filter(
            AdminSessionTable.admin_id == admin_id,
            AdminSessionTable.is_login == True
        ).first()

        if not session:
            raise HTTPException(status_code=401, detail="Session not found or expired")

        # Verify refresh token hash
        if not Hashing.verify_hash(refresh_token, session.refresh_token_hash):
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        # Get permissions based on role
        permissions = ROLE_PERMISSIONS.get(AdminRole(admin.role), [])

        # Generate new tokens
        access_token = token_service.create_access_token(data={
            "admin_id": admin.admin_id,
            "email": admin.email,
            "role": admin.role,
            "permissions": permissions,
            "android_id": android_id or payload.get("android_id"),
            "uuid": uuid or payload.get("uuid")
        })

        new_refresh_token = token_service.create_refresh_token(data={
            "admin_id": admin.admin_id,
            "email": admin.email,
            "role": admin.role,
            "permissions": permissions,
            "android_id": android_id or payload.get("android_id"),
            "uuid": uuid or payload.get("uuid")
        })

        # Update session with new token hashes
        session.access_token_hash = Hashing.create_hash(access_token)
        session.refresh_token_hash = Hashing.create_hash(new_refresh_token)
        db.commit()

        return GlobalResponse(
            success=True,
            message="Token refreshed successfully",
            data={
                "access_token": access_token,
                "refresh_token": new_refresh_token
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")





# ==============================================================================
"""
Get admin profile

request example
get /profile

response example
{
    "success": true,
    "message": "Profile retrieved successfully",
    "data": {
        "admin_id": "admin_id",
        "email": "admin@example.com",
        "full_name": "Admin Name",
        "role": "super_admin",
        "permissions": ["can_view_users", ...],
        "is_active": true,
        "is_super_admin": true,
        "profile_image_url": null,
        "last_login_at": "2023-01-01T00:00:00Z",
        "created_at": "2023-01-01T00:00:00Z"
    }
}
"""
# ==============================================================================

@admin_auth_router.get("/profile-data", response_model=GlobalResponse)
async def get_admin_profile(
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)):
    try:
        return GlobalResponse(
            success=True,
            message="Profile retrieved successfully",
            data={
                "admin_id": current_admin.admin_id,
                "email": current_admin.email,
                "full_name": current_admin.full_name,
                "role": current_admin.role,
                "permissions": ROLE_PERMISSIONS.get(AdminRole(current_admin.role), []),
                "is_active": current_admin.is_active,
                "is_super_admin": current_admin.is_super_admin,
                "profile_image_url": current_admin.profile_image_url,
                "last_login_at": current_admin.last_login_at,
                "created_at": current_admin.created_at
            }
        )

    except HTTPException:
        raise

    except Exception as e:
        print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
        raise HTTPException(status_code=500, detail="Internal server error")





"""
Update own profile

request example
put {
    "full_name": "Admin Name",
    "email": "admin@example.com",
    "profile_image_url": null
}
"""
# ==============================================================================

@admin_auth_router.put("/profile", response_model=GlobalResponse)
async def update_own_profile(
    request: AdminSelfUpdateRequest,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)):
    try:
        if request.email and request.email != current_admin.email:
            existing_admin = db.query(AdminTable).filter(AdminTable.email == request.email).first()
            if existing_admin:
                raise HTTPException(status_code=409, detail="Admin with this email already exists")
            current_admin.email = request.email

        if request.full_name is not None:
            current_admin.full_name = request.full_name
        if request.profile_image_url is not None:
            current_admin.profile_image_url = request.profile_image_url

        current_admin.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(current_admin)

        return GlobalResponse(
            success=True,
            message="Profile updated successfully",
            data={
                "admin_id": current_admin.admin_id,
                "email": current_admin.email,
                "full_name": current_admin.full_name,
                "profile_image_url": current_admin.profile_image_url,
                "role": current_admin.role,
                "is_active": current_admin.is_active,
                "is_super_admin": current_admin.is_super_admin,
                "updated_at": current_admin.updated_at
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")




# ==============================================================================
"""
Create new admin (super_admin only)

request example
post {
    "email": "newadmin@example.com",
    "password": "securepassword",
    "full_name": "New Admin",
    "role": "moderator",
    "profile_image_url": null
}

response example
{
    "success": true,
    "message": "Admin created successfully",
    "data": {
        "admin_id": "admin_id",
        "email": "newadmin@example.com",
        "full_name": "New Admin",
        "role": "moderator"
    }
}
"""

# ==============================================================================

@admin_auth_router.post("/create", response_model=GlobalResponse)
async def create_admin(
    request: AdminCreateRequest,
    request_info: Request,
    current_admin=Depends(require_super_admin),
    db: Session = Depends(get_db)):
    try:
        # Check if email already exists
        existing_admin = db.query(AdminTable).filter(AdminTable.email == request.email).first()
        if existing_admin:
            raise HTTPException(status_code=409, detail="Admin with this email already exists")
        
        # Create new admin
        admin_id = Generators.generate_user_id()  # Using same generator for admin IDs
        password_hash = Hashing.create_hash(request.password)
        
        new_admin = AdminTable(
            admin_id=admin_id,
            email=request.email,
            password_hash=password_hash,
            full_name=request.full_name,
            profile_image_url=request.profile_image_url,
            role=request.role.value,
            is_active=True,
            is_super_admin=False
        )
        
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)
        
        # Request info
        ip = request_info.client.host
        
        # Log the creation
        new_notification = AdminSessionTable(
            admin_id=admin_id,
            session_id=f"created_by_{current_admin.admin_id}",
            device_uuid=None,
            device_id=None,
            last_ip_address=ip,
            login_at=datetime.now(timezone.utc),
            logout_at=datetime.now(timezone.utc),
            is_login=False
        )
        db.add(new_notification)
        db.commit()
        
        return GlobalResponse(
            success=True,
            message="Admin created successfully",
            data={
                "admin_id": new_admin.admin_id,
                "email": new_admin.email,
                "full_name": new_admin.full_name,
                "role": new_admin.role
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")





# ==============================================================================
"""
List all admins (super_admin only)

request example
get /admin/list?page=1&limit=20&role=moderator&is_active=true

response example
{
    "success": true,
    "message": "Admins retrieved successfully",
    "data": {
        "admins": [...]
    },
    "pagination": {
        "page": 1,
        "limit": 20,
        "total": 10,
        "total_pages": 1
    }
}
"""
# ==============================================================================

@admin_auth_router.get("/list", response_model=GlobalResponse)
async def list_admins(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    role: Optional[AdminRoleEnum] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    current_admin=Depends(require_super_admin),
    db: Session = Depends(get_db)):
    try:
        query = db.query(AdminTable)
        
        # Apply filters
        if role:
            query = query.filter(AdminTable.role == role.value)
        if is_active is not None:
            query = query.filter(AdminTable.is_active == is_active)
        if search:
            query = query.filter(
                or_(
                    AdminTable.email.ilike(f"%{search}%"),
                    AdminTable.full_name.ilike(f"%{search}%"),
                    AdminTable.admin_id.ilike(f"%{search}%")
                )
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        admins = query.order_by(desc(AdminTable.created_at)).offset(offset).limit(limit).all()
        
        # Format response
        admin_list = []
        for admin in admins:
            admin_list.append({
                "admin_id": admin.admin_id,
                "email": admin.email,
                "full_name": admin.full_name,
                "role": admin.role,
                "is_active": admin.is_active,
                "is_super_admin": admin.is_super_admin,
                "last_login_at": admin.last_login_at,
                "created_at": admin.created_at
            })
        
        return GlobalResponse(
            success=True,
            message="Admins retrieved successfully",
            data={"admins": admin_list},
            pagination={
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")





# ==============================================================================
"""
Update admin details (super_admin only)

request example
put {
    "full_name": "Updated Name",
    "role": "viewer",
    "is_active": true
}

response example
{
    "success": true,
    "message": "Admin updated successfully",
    "data": {
        "admin_id": "admin_id",
        "full_name": "Updated Name",
        "role": "viewer",
        "is_active": true
    }
}
"""
# ==============================================================================

@admin_auth_router.put("/{admin_id}", response_model=GlobalResponse)
async def update_admin(
    admin_id: str,
    request: AdminUpdateRequest,
    current_admin=Depends(require_super_admin),
    db: Session = Depends(get_db)):
    try:
        # Cannot modify yourself
        if admin_id == current_admin.admin_id:
            raise HTTPException(status_code=400, detail="Cannot modify your own account")
        
        admin = db.query(AdminTable).filter(AdminTable.admin_id == admin_id).first()
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")
        
        # Prevent changing the last super_admin
        if admin.is_super_admin and admin.role == AdminRole.SUPER_ADMIN.value:
            if request.role and request.role != AdminRoleEnum.SUPER_ADMIN:
                raise HTTPException(status_code=400, detail="Cannot change role of the last super admin")
            if request.is_active is False:
                raise HTTPException(status_code=400, detail="Cannot deactivate the last super admin")
        
        # Update fields
        if request.full_name is not None:
            admin.full_name = request.full_name
        if request.role is not None:
            admin.role = request.role.value
        if request.is_active is not None:
            admin.is_active = request.is_active
        if request.profile_image_url is not None:
            admin.profile_image_url = request.profile_image_url
        
        admin.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(admin)
        
        return GlobalResponse(
            success=True,
            message="Admin updated successfully",
            data={
                "admin_id": admin.admin_id,
                "full_name": admin.full_name,
                "role": admin.role,
                "is_active": admin.is_active
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")






# ==============================================================================
"""
Reset admin password (super_admin only)

request example
post {
    "new_password": "newsecurepassword"
}

response example
{
    "success": true,
    "message": "Password reset successfully",
    "data": {}
}
"""
# ==============================================================================

@admin_auth_router.post("/{admin_id}/reset-password", response_model=GlobalResponse)
async def reset_admin_password(
    admin_id: str,
    request: AdminPasswordUpdateRequest,
    current_admin=Depends(require_super_admin),
    db: Session = Depends(get_db)):
    try:
        admin = db.query(AdminTable).filter(AdminTable.admin_id == admin_id).first()
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")
        
        # Update password
        admin.password_hash = Hashing.create_hash(request.new_password)
        admin.updated_at = datetime.now(timezone.utc)
        
        # Invalidate all sessions for this admin
        db.query(AdminSessionTable).filter(
            AdminSessionTable.admin_id == admin_id,
            AdminSessionTable.is_login == True
        ).update({
            "is_login": False,
            "logout_at": datetime.now(timezone.utc)
        })
        
        db.commit()
        
        return GlobalResponse(
            success=True,
            message="Password reset successfully. Admin will need to login again.",
            data={}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ==============================================================================
"""
Delete/Deactivate admin (super_admin only)

request example
delete

response example
{
    "success": true,
    "message": "Admin deactivated successfully",
    "data": {}
}
"""
# ==============================================================================

@admin_auth_router.delete("/{admin_id}", response_model=GlobalResponse)
async def delete_admin(
    admin_id: str,
    current_admin=Depends(require_super_admin),
    db: Session = Depends(get_db)):
    try:
        # Cannot delete yourself
        if admin_id == current_admin.admin_id:
            raise HTTPException(status_code=400, detail="Cannot delete your own account")
        
        admin = db.query(AdminTable).filter(AdminTable.admin_id == admin_id).first()
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")
        
        # Prevent deleting the last super_admin
        if admin.is_super_admin:
            super_admin_count = db.query(AdminTable).filter(
                AdminTable.is_super_admin == True,
                AdminTable.is_active == True
            ).count()
            if super_admin_count <= 1:
                raise HTTPException(status_code=400, detail="Cannot delete the last super admin")
        
        # Soft delete - deactivate instead of actual deletion
        admin.is_active = False
        admin.updated_at = datetime.now(timezone.utc)
        
        # Invalidate all sessions
        db.query(AdminSessionTable).filter(
            AdminSessionTable.admin_id == admin_id,
            AdminSessionTable.is_login == True
        ).update({
            "is_login": False,
            "logout_at": datetime.now(timezone.utc)
        })
        
        db.commit()
        
        return GlobalResponse(
            success=True,
            message="Admin deactivated successfully",
            data={}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")





# ==============================================================================
"""
Change own password

request example
post {
    "current_password": "oldpassword",
    "new_password": "newpassword"
}

response example
{
    "success": true,
    "message": "Password changed successfully",
    "data": {}
}
"""
# ==============================================================================

@admin_auth_router.post("/change-password", response_model=GlobalResponse)
async def change_own_password(
    request: AdminPasswordUpdateRequest,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)):
    try:
        # Verify current password
        if not Hashing.verify_password(request.current_password, current_admin.password_hash):
            raise HTTPException(status_code=401, detail="Current password is incorrect")
        
        # Update password
        current_admin.password_hash = Hashing.create_hash(request.new_password)
        current_admin.updated_at = datetime.now(timezone.utc)
        
        # Invalidate all sessions except current
        db.query(AdminSessionTable).filter(
            AdminSessionTable.admin_id == current_admin.admin_id,
            AdminSessionTable.is_login == True
        ).update({
            "is_login": False,
            "logout_at": datetime.now(timezone.utc)
        })
        
        db.commit()
        
        return GlobalResponse(
            success=True,
            message="Password changed successfully. Please login again.",
            data={}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")



# ==============================================================================
"""
Get user details (all admin roles)

request example
get /users/{user_id}

response example
{
    "success": true,
    "message": "User details retrieved successfully",
    "data": {
        "user": {...},
        "wallet": {...},
        "settings": {...}
    }
}
"""
# ==============================================================================

@admin_auth_router.get("/users/{user_id}", response_model=GlobalResponse)
async def get_user_details(
    user_id: str,
    current_admin=Depends(require_permission(AdminPermissions.CAN_VIEW_USERS)),
    db: Session = Depends(get_db)):
    try:
        user = db.query(UserTable).filter(UserTable.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        wallet = db.query(WalletTable).filter(WalletTable.user_id == user_id).first()
        settings = db.query(SettingsTable).filter(SettingsTable.user_id == user_id).first()
        
        return GlobalResponse(
            success=True,
            message="User details retrieved successfully",
            data={
                "user": {
                    "user_id": user.user_id,
                    "full_name": user.full_name,
                    "email": user.email_address,
                    "phone": user.phone_number,
                    "profile_image_url": user.profile_image_url,
                    "phone_verified": user.phone_verified,
                    "email_verified": user.email_verified,
                    "created_at": user.created_at,
                    "updated_at": user.updated_at
                },
                "wallet": {
                    "user_id": wallet.user_id if wallet else None,
                    "balance": wallet.balance if wallet else 0,
                    "currency": wallet.currency if wallet else "BDT",
                    "last_updated": wallet.last_updated if wallet else None
                },
                "settings": {
                    "allow_notifications": settings.allow_notifications if settings else True,
                    "dark_mode": settings.dark_mode if settings else False,
                    "language": settings.language if settings else "en",
                    "account_locked": settings.account_locked if settings else False,
                    "kyc_status": settings.kyc_status,
                    "kyc_verified_at": settings.kyc_verified_at,
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ==============================================================================
"""
Update user status (lock/unlock) - moderator+ only

request example
put /users/{user_id}/status
{
    "is_active": false,
    "reason": "Suspicious activity detected"
}

response example
{
    "success": true,
    "message": "User status updated successfully",
    "data": {
        "user_id": "user_id",
        "is_active": false
    }
}
"""
# ==============================================================================

@admin_auth_router.put("/users/{user_id}/status", response_model=GlobalResponse)
async def update_user_status(
    user_id: str,
    request: UserUpdateStatusRequest,
    current_admin=Depends(require_permission(AdminPermissions.CAN_LOCK_USERS)),
    db: Session = Depends(get_db)):
    try:
        user = db.query(SettingsTable).filter(
            SettingsTable.user_id == user_id
        ).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        old_status = user.account_locked
        user.account_locked = request.is_active
        user.updated_at = datetime.now(timezone.utc)
        
        # Update settings
        settings = db.query(SettingsTable).filter(SettingsTable.user_id == user_id).first()
        if settings:
            settings.account_locked = not request.is_active
        
        db.commit()
        
        # Create notification for user
        from app.model.notification_table import NotificationTable
        from app.enums import NotificationType
        
        notification = NotificationTable(
            target_id=user_id,
            type=NotificationType.ALERT,
            title="Account Status Changed",
            body=f"Your account has been {'activated' if request.is_active else 'deactivated'}. Reason: {request.reason or 'No reason provided'}"
        )
        db.add(notification)
        db.commit()
        
        return GlobalResponse(
            success=True,
            message="User status updated successfully",
            data={
                "user_id": user_id,
                "previous_status": old_status,
                "is_active": request.is_active,
                "reason": request.reason
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")




# ==============================================================================
"""
Send notification/email to user (moderator+)

request example
post /users/{user_id}/notify
{
    "title": "Account Notice",
    "message": "Your account details were updated",
    "notification_type": "alert",
    "send_push": true,
    "send_email": true
}
"""
# ==============================================================================

@admin_auth_router.post("/users/{user_id}/notify", response_model=GlobalResponse)
async def notify_user(
    user_id: str,
    request: AdminUserNotifyRequest,
    background_tasks: BackgroundTasks,
    current_admin=Depends(require_permission(AdminPermissions.CAN_EDIT_USERS)),
    db: Session = Depends(get_db)
):
    try:
        user = db.query(UserTable).filter(
            UserTable.user_id == user_id
        ).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        settings = db.query(SettingsTable).filter(SettingsTable.user_id == user_id).first()
        push_allowed = request.send_push and (settings.allow_notifications if settings else True)

        # Store notification in DB
        notification = NotificationTable(
            target_id=user_id,
            type=request.notification_type,
            title=request.title,
            body=request.message,
            img_url=request.image_url,
            meta_data={
                "button_text": request.button_text,
                "button_link": request.button_link,
                "send_push": push_allowed,
                "send_email": request.send_email,
                "send_sms": request.send_sms,
            },
            creator=current_admin.admin_id
        )
        db.add(notification)
        db.commit()

        notification_service = NotificationServices(
            db=db,
            background_tasks=background_tasks
        )
        notification_service.send_notification(NotificationData(
            user_id=user_id,
            title=request.title,
            body=request.message,
            noty_type=request.notification_type,
            data={
                "button_text": request.button_text,
                "button_link": request.button_link,
            },
            image_url=request.image_url,
            push=push_allowed,
            email=request.send_email,
            sms=request.send_sms
        ))

        return GlobalResponse(
            success=True,
            message="Notification queued successfully",
            data={
                "user_id": user_id,
                "title": request.title,
                "send_push": push_allowed,
                "send_email": request.send_email,
                "send_sms": request.send_sms
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ==============================================================================
# ==============================================================================


# ==============================================================================
"""
Refund transaction (super_admin only)

request example
post /transactions/{transaction_id}/refund
{
    "reason": "User requested refund due to service issue",
    "reference_id": "ref123"
}

response example
{
    "success": true,
    "message": "Transaction refunded successfully",
    "data": {
        "transaction_id": "tx_id",
        "action": "refund",
        "status": "refunded",
        "refund_amount": 100.0
    }
}
"""
# ==============================================================================

@admin_auth_router.post("/transactions/{transaction_id}/refund", response_model=GlobalResponse)
async def refund_transaction(
    transaction_id: str,
    request: TransactionActionRequest,
    current_admin=Depends(require_permission(AdminPermissions.CAN_REFUND_TRANSACTIONS)),
    db: Session = Depends(get_db)):
    try:
        transaction = db.query(TransactionTable).filter(
            TransactionTable.transaction_id == transaction_id
        ).first()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        if transaction.status != TransactionStatus.SUCCESS.value:
            raise HTTPException(status_code=400, detail=f"Can only refund successful transactions. Current status: {transaction.status}")
        
        # Update transaction status
        transaction.status = TransactionStatus.REFUNDED.value
        transaction.updated_at = datetime.now(timezone.utc)
        
        # Credit back to sender
        sender_wallet = db.query(WalletTable).filter(
            WalletTable.user_id == transaction.sender_user_id
        ).first()
        
        refund_amount = float(transaction.amount)
        
        if sender_wallet:
            sender_wallet.balance += Decimal(str(transaction.amount))
            sender_wallet.last_updated = datetime.now(timezone.utc)
        
        # Create refund transaction record
        refund_tx = TransactionTable(
            transaction_id=Generators.generate_transaction_id(),
            sender_user_id="SYSTEM_REFUND",
            receiver_user_id=transaction.sender_user_id,
            transaction_type="refund",
            amount=transaction.amount,
            currency=transaction.currency,
            status=TransactionStatus.SUCCESS.value,
            description=f"Refund for transaction {transaction_id}. Reason: {request.reason}",
            reference_id=transaction_id,
            fee=0,
            net_amount=transaction.amount
        )
        db.add(refund_tx)
        db.commit()
        
        return GlobalResponse(
            success=True,
            message="Transaction refunded successfully",
            data={
                "transaction_id": transaction_id,
                "action": "refund",
                "status": TransactionStatus.REFUNDED.value,
                "refund_amount": refund_amount,
                "reason": request.reason,
                "processed_by": current_admin.admin_id,
                "processed_at": datetime.now(timezone.utc)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ==============================================================================
# ==============================================================================





# ==============================================================================
"""
Get wallet details (all admin roles)

request example
get /wallets/{user_id}

response example
{
    "success": true,
    "message": "Wallet details retrieved successfully",
    "data": {...}
}
"""
# ==============================================================================

@admin_auth_router.get("/wallets/{user_id}", response_model=GlobalResponse)
async def get_wallet_details(
    user_id: str,
    current_admin=Depends(require_permission(AdminPermissions.CAN_VIEW_WALLETS)),
    db: Session = Depends(get_db)):
    try:
        wallet = db.query(WalletTable).filter(WalletTable.user_id == user_id).first()
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        
        user = db.query(UserTable).filter(UserTable.user_id == user_id).first()
        
        # Get recent transactions
        recent_txs = db.query(TransactionTable).filter(
            or_(
                TransactionTable.sender_user_id == user_id,
                TransactionTable.receiver_user_id == user_id
            )
        ).order_by(desc(TransactionTable.created_at)).limit(10).all()
        
        return GlobalResponse(
            success=True,
            message="Wallet details retrieved successfully",
            data={
                "user_id": wallet.user_id,
                "full_name": user.full_name if user else "Unknown",
                "email": user.email if user else "Unknown",
                "phone": user.phone if user else "Unknown",
                "balance": float(wallet.balance),
                "currency": wallet.currency,
                "last_updated": wallet.last_updated,
                "recent_transactions": [
                    {
                        "transaction_id": tx.transaction_id,
                        "type": tx.transaction_type,
                        "amount": float(tx.amount),
                        "status": tx.status,
                        "created_at": tx.created_at
                    }
                    for tx in recent_txs
                ]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ==============================================================================
"""
Adjust wallet balance (super_admin only)

request example
post /wallets/{user_id}/adjust
{
    "amount": 500.0,  // Positive for credit, negative for debit
    "reason": "Bonus for loyalty",
    "reference_id": "bonus_001"
}

response example
{
    "success": true,
    "message": "Wallet adjusted successfully",
    "data": {
        "user_id": "user_id",
        "previous_balance": 1000.0,
        "adjusted_amount": 500.0,
        "new_balance": 1500.0
    }
}
"""
# ==============================================================================

@admin_auth_router.post("/wallets/{user_id}/adjust", response_model=GlobalResponse)
async def adjust_wallet_balance(
    user_id: str,
    request: WalletAdjustmentRequest,
    current_admin=Depends(require_permission(AdminPermissions.CAN_ADJUST_WALLETS)),
    db: Session = Depends(get_db)):
    try:
        wallet = db.query(WalletTable).filter(WalletTable.user_id == user_id).first()
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        
        previous_balance = float(wallet.balance)
        adjustment_amount = Decimal(str(request.amount))
        
        # Calculate new balance
        new_balance = wallet.balance + adjustment_amount
        
        if new_balance < 0:
            raise HTTPException(status_code=400, detail="Insufficient balance for debit operation")
        
        # Update wallet
        wallet.balance = new_balance
        wallet.last_updated = datetime.now(timezone.utc)
        
        # Create transaction record
        adjustment_type = "credit" if request.amount > 0 else "debit"
        tx = TransactionTable(
            transaction_id=Generators.generate_transaction_id(),
            sender_user_id=f"SYSTEM_{adjustment_type.upper()}" if request.amount < 0 else "SYSTEM_ADJUST",
            receiver_user_id=user_id if request.amount > 0 else f"SYSTEM_DEBIT",
            transaction_type=f"wallet_{adjustment_type}",
            amount=abs(adjustment_amount),
            currency=wallet.currency,
            status=TransactionStatus.SUCCESS.value,
            description=f"Wallet adjustment: {request.reason}",
            reference_id=request.reference_id,
            fee=0,
            net_amount=abs(adjustment_amount)
        )
        db.add(tx)
        db.commit()
        
        return GlobalResponse(
            success=True,
            message="Wallet adjusted successfully",
            data={
                "user_id": user_id,
                "previous_balance": previous_balance,
                "adjusted_amount": request.amount,
                "new_balance": float(new_balance),
                "currency": wallet.currency,
                "reason": request.reason,
                "transaction_id": tx.transaction_id,
                "adjusted_by": current_admin.admin_id,
                "adjusted_at": datetime.now(timezone.utc)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ==============================================================================
# ==============================================================================
