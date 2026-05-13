import os, pytz
from fastapi import APIRouter, HTTPException, Depends, Request, Query, BackgroundTasks, Header
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from sqlalchemy import or_, and_, func, desc
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from decimal import Decimal

from app.core.database import get_db

from app.model.admin_table import AdminTable, AdminRole, ROLE_PERMISSIONS, AdminPermissions

from app.utils import Generators
from app.constants import AnsiColor
from app.model import AdminSessionTable, UserTable, WalletTable, TransactionTable, SettingsTable
from app.enums import TransactionStatus, ActivityStatus
from app.schema import GlobalResponse

from admin.schema.admin_schema import *

from app.dependencies.admin_auth import (
    get_current_admin,
    require_permission,
    require_super_admin,
    require_moderator_or_higher
)

from app.services.admin.admin_services import AdminManagementServices
from app.services.admin.access_services import AdminAccessServices



admin_access_router = APIRouter()

today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)




# ==============================================================================

@admin_access_router.get("/dashboard/stats", response_model=GlobalResponse)
async def get_dashboard_stats(
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    adminAccessServices = AdminAccessServices(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return adminAccessServices.get_dashboard_stats()




# ==============================================================================
"""
List users with filtering (all admin roles)

request example
get /users?page=1&limit=20&search=john&kyc_status=verified

response example
{
    "success": true,
    "message": "Users retrieved successfully",
    "data": {
        "users": [...]
    },
    "pagination": {...}
}
"""
# ==============================================================================

@admin_access_router.get("/users-list")
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    kyc_status: Optional[str] = None,
    is_active: Optional[bool] = None,
    sort_by: Optional[str] = Query("created_at", regex="^(created_at|full_name|wallet_balance)$"),
    sort_order: Optional[str] = Query("desc", regex="^(asc|desc)$"),
    current_admin: AdminTable = Depends(get_current_admin),
    db: Session = Depends(get_db)):
    try:
        # Build query with joins
        query = db.query(UserTable).join(SettingsTable).join(WalletTable)
        
        # Apply filters
        if search:
            query = query.filter(
                or_(
                    UserTable.full_name.ilike(f"%{search}%"),
                    UserTable.email_address.ilike(f"%{search}%"),
                    UserTable.phone_number.ilike(f"%{search}%"),
                    UserTable.user_id.ilike(f"%{search}%")
                )
            )
        if kyc_status:
            query = query.filter(SettingsTable.kyc_status == kyc_status)
        if is_active is not None:
            query = query.filter(SettingsTable.account_locked == (not is_active))
        
        # Get total count
        total = query.count()
        
        # Apply sorting
        if sort_by == "created_at":
            sort_column = UserTable.created_at
        elif sort_by == "full_name":
            sort_column = UserTable.full_name
        elif sort_by == "wallet_balance":
            sort_column = WalletTable.balance
        
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        # Apply pagination
        offset = (page - 1) * limit
        users = query.offset(offset).limit(limit).all()
        
        # Format response
        user_list = []
        for user in users:
            wallet = db.query(WalletTable).filter(WalletTable.user_id == user.user_id).first()
            settings = db.query(SettingsTable).filter(SettingsTable.user_id == user.user_id).first()

            user_list.append({
                "user_id": user.user_id,
                "full_name": user.full_name,
                "email": user.email_address,
                "phone": user.country_code+user.phone_number,
                "profile_image_url": user.profile_image_url,
                "phone_verified": user.phone_verified,
                "email_verified": user.email_verified,
                "kyc_status": settings.kyc_status if settings else "pending",
                "is_active": not settings.account_locked if settings else False,
                "wallet_balance": float(wallet.balance) if wallet else 0,
                "wallet_currency": wallet.currency if wallet else "BDT",
                "created_at": user.created_at
            })
        
        return GlobalResponse(
            success=True,
            message="Users retrieved successfully",
            data={"users": user_list},
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
        print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
        raise HTTPException(status_code=500, detail="Internal server error")





# ==============================================================================
"""
List transactions with filtering (all admin roles)

request example
get /transactions-list?page=1&limit=20&status=success&type=deposit

response example
{
    "success": true,
    "message": "Transactions retrieved successfully",
    "data": {"transactions": [...]},
    "pagination": {...}
}
"""
# ==============================================================================

@admin_access_router.get("/transactions-list", response_model=GlobalResponse)
async def list_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    transaction_id: Optional[str] = None,
    sender_id: Optional[str] = None,
    receiver_id: Optional[str] = None,
    transaction_type: Optional[str] = None,
    status: Optional[str] = None,
    created_from: Optional[datetime] = None,
    created_to: Optional[datetime] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    current_admin=Depends(require_permission(AdminPermissions.CAN_VIEW_TRANSACTIONS)),
    db: Session = Depends(get_db)):
    try:
        query = db.query(TransactionTable)
        
        # Apply filters
        if search:
            query = query.filter(
                or_(
                    TransactionTable.transaction_id.ilike(f"%{search}%"),
                    TransactionTable.sender_user_id.ilike(f"%{search}%"),
                    TransactionTable.receiver_user_id.ilike(f"%{search}%"),
                    TransactionTable.reference.ilike(f"%{search}%"),
                    TransactionTable.account_name.ilike(f"%{search}%")
                )
            )
        if transaction_id:
            query = query.filter(TransactionTable.transaction_id == transaction_id)
        if sender_id:
            query = query.filter(TransactionTable.sender_user_id.ilike(f"%{sender_id}%"))
        if receiver_id:
            query = query.filter(TransactionTable.receiver_user_id.ilike(f"%{receiver_id}%"))
        if transaction_type:
            query = query.filter(TransactionTable.transaction_type == transaction_type)
        if status:
            query = query.filter(TransactionTable.status == status)
        if created_from:
            query = query.filter(TransactionTable.created_at >= created_from)
        if created_to:
            query = query.filter(TransactionTable.created_at <= created_to)
        if min_amount is not None:
            query = query.filter(TransactionTable.amount >= min_amount)
        if max_amount is not None:
            query = query.filter(TransactionTable.amount <= max_amount)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        transactions = query.order_by(desc(TransactionTable.created_at)).offset(offset).limit(limit).all()
        
        # Format response
        transaction_list = []
        for tx in transactions:
            transaction_list.append({
                "transaction_id": tx.transaction_id,
                "sender_user_id": tx.sender_user_id,
                "receiver_user_id": tx.receiver_user_id,
                "transaction_type": tx.transaction_type.value if tx.transaction_type else None,
                "amount": float(tx.amount),
                "currency": tx.currency,
                "status": tx.status.value if tx.status else None,
                "description": tx.reference or "",
                "created_at": tx.created_at.isoformat() if tx.created_at else None
            })
        
        return GlobalResponse(
            success=True,
            message="Transactions retrieved successfully",
            data={"transactions": transaction_list},
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
Get transaction details (all admin roles)

request example
get /transactions/{transaction_id}

response example
{
    "success": true,
    "message": "Transaction details retrieved successfully",
    "data": {...}
}
"""
# ==============================================================================

@admin_access_router.get("/transactions/{transaction_id}", response_model=GlobalResponse)
async def get_transaction_details(
    transaction_id: str,
    current_admin=Depends(require_permission(AdminPermissions.CAN_VIEW_TRANSACTIONS)),
    db: Session = Depends(get_db)):
    try:
        transaction = db.query(TransactionTable).filter(
            TransactionTable.transaction_id == transaction_id
        ).first()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        return GlobalResponse(
            success=True,
            message="Transaction details retrieved successfully",
            data={
                "transaction_id": transaction.transaction_id,
                "sender_user_id": transaction.sender_user_id,
                "receiver_user_id": transaction.receiver_user_id,
                "transaction_type": transaction.transaction_type,
                "amount": float(transaction.amount),
                "currency": transaction.currency,
                "status": transaction.status,
                "description": transaction.description,
                "fee": float(transaction.fee) if transaction.fee else 0,
                "net_amount": float(transaction.net_amount) if transaction.net_amount else 0,
                "reference_id": transaction.reference_id,
                "created_at": transaction.created_at,
                "updated_at": transaction.updated_at
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")






# ==============================================================================
"""
Cancel transaction (super_admin + moderator)

request example
post /transactions/{transaction_id}/cancel
{
    "reason": "Duplicate transaction requested by user",
    "reference_id": "ref123"
}

response example
{
    "success": true,
    "message": "Transaction cancelled successfully",
    "data": {
        "transaction_id": "tx_id",
        "action": "cancel",
        "status": "cancelled"
    }
}
"""
# ==============================================================================

@admin_access_router.post("/transactions/{transaction_id}/cancel", response_model=GlobalResponse)
async def cancel_transaction(
    transaction_id: str,
    request: TransactionActionRequest,
    current_admin=Depends(require_permission(AdminPermissions.CAN_CANCEL_TRANSACTIONS)),
    db: Session = Depends(get_db)):
    try:
        transaction = db.query(TransactionTable).filter(
            TransactionTable.transaction_id == transaction_id
        ).first()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        if transaction.status not in [TransactionStatus.PENDING.value, TransactionStatus.SUCCESS.value]:
            raise HTTPException(status_code=400, detail=f"Cannot cancel transaction with status: {transaction.status}")
        
        # Update transaction status
        old_status = transaction.status
        transaction.status = TransactionStatus.CANCELLED.value
        transaction.updated_at = datetime.now(timezone.utc)
        
        # If transaction was successful, refund to sender
        if old_status == TransactionStatus.SUCCESS.value:
            sender_wallet = db.query(WalletTable).filter(
                WalletTable.user_id == transaction.sender_user_id
            ).first()
            
            if sender_wallet:
                # Credit back the amount (including fee reversal logic could be added)
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
                    description=f"Refund for cancelled transaction {transaction_id}",
                    reference_id=transaction_id,
                    fee=0,
                    net_amount=transaction.amount
                )
                db.add(refund_tx)
        
        db.commit()
        
        return GlobalResponse(
            success=True,
            message="Transaction cancelled successfully",
            data={
                "transaction_id": transaction_id,
                "action": "cancel",
                "previous_status": old_status,
                "status": TransactionStatus.CANCELLED.value,
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
"""
List wallets with filtering (all admin roles)

request example
get /wallets-list?page=1&limit=20&search=john

response example
{
    "success": true,
    "message": "Wallets retrieved successfully",
    "data": {"wallets": [...]},
    "pagination": {...}
}
"""
# ==============================================================================

@admin_access_router.get("/wallets-list", response_model=GlobalResponse)
async def list_wallets(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    min_balance: Optional[float] = None,
    max_balance: Optional[float] = None,
    current_admin=Depends(require_permission(AdminPermissions.CAN_VIEW_WALLETS)),
    db: Session = Depends(get_db)):
    try:
        # Join query for wallets with users
        query = db.query(WalletTable).join(UserTable)
        
        # Apply filters
        if search:
            query = query.filter(
                or_(
                    UserTable.full_name.ilike(f"%{search}%"),
                    UserTable.email_address.ilike(f"%{search}%"),
                    UserTable.phone_number.ilike(f"%{search}%"),
                    WalletTable.user_id.ilike(f"%{search}%")
                )
            )
        if min_balance is not None:
            query = query.filter(WalletTable.balance >= min_balance)
        if max_balance is not None:
            query = query.filter(WalletTable.balance <= max_balance)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        wallets = query.order_by(desc(WalletTable.last_updated)).offset(offset).limit(limit).all()
        
        # Format response
        wallet_list = []
        for wallet in wallets:
            user = db.query(UserTable).filter(UserTable.user_id == wallet.user_id).first()
            wallet_list.append({
                "user_id": wallet.user_id,
                "full_name": user.full_name if user else "Unknown",
                "email": user.email_address if user else "Unknown",
                "phone": user.phone_number if user else "Unknown",
                "balance": float(wallet.balance),
                "currency": wallet.currency,
                "last_updated": wallet.last_updated.isoformat() if wallet.last_updated else None
            })
        
        return GlobalResponse(
            success=True,
            message="Wallets retrieved successfully",
            data={"wallets": wallet_list},
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
# ==============================================================================
