from fastapi import APIRouter, Depends, BackgroundTasks, Query, Header, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.schema import (
    BillProviderCreateRequest,
    PayBillRequest,
    BillHistoryRequest,
    BillTransactionDetailsRequest
)
from app.schema.global_schema import GlobalResponse
from app.services.wallet.bill_services import BillServices


from app.enums.notification_enum import NotificationType




bill_router = APIRouter()




# ==============================================================================

@bill_router.get("/providers")
async def get_bill_providers(
    category: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    bill_service = BillServices(
        db=db,
        background_tasks=None,
        request=None,
        authorization=authorization
    )
    
    return bill_service.get_bill_providers(
        category=category,
        status=status,
        search=search,
        page=page,
        limit=limit
    )




# ==============================================================================

@bill_router.get("/providers/{category}")
async def get_bill_categories(
    category: str, 
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    bill_service = BillServices(db=db, background_tasks=None, request=None, authorization=authorization)
    return bill_service.get_bill_categories(category=category)




# ==============================================================================

@bill_router.post("/pay-bill")
async def pay_bill(
    request: PayBillRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    bill_service = BillServices(
        db=db,
        background_tasks=background_tasks,
        request=None,
        authorization=None
    )
    
    return bill_service.pay_bill(request=request)




# ==============================================================================

@bill_router.post("/new-provider")
async def add_bill_provider(
    request: BillProviderCreateRequest, 
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    bill_service = BillServices(
        db=db, 
        background_tasks=background_tasks, 
        request=None, authorization=authorization
    )

    return bill_service.add_bill_provider(request=request)




# ==============================================================================
# ==============================================================================
