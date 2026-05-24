import dotenv

from fastapi import APIRouter, Depends, BackgroundTasks, Header, Request
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.services.wallet.donation_services import DonationServices
from app.schema.donations_schema import DonationsRequest, DonationOut, DonationOrgRequest, DonationOrgRemoveRequest
from app.schema.global_schema import GlobalResponse



donation_router = APIRouter()
dotenv.load_dotenv()





# ==============================================================================

@donation_router.get("/organization")
async def get_donations(
    db: Session = Depends(get_db),
    request_info: Request = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    authorization: str = Header(None)
):
    donation_service = DonationServices(
        db=db,
        background_tasks=background_tasks,
        request=request_info,
        authorization=authorization
    )

    return donation_service.get_donations()




# ==============================================================================

@donation_router.post("/donate")
async def make_donation(
    payload: DonationsRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """"""
    donation_service = DonationServices(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )
    
    return donation_service.make_donation(payload=payload)





# ==============================================================================
@donation_router.post("/new-organization")
async def organization_request(
    request: DonationOrgRequest,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    request_info: Request = None,
    authorization: str = Header(None)
):
    donation_service = DonationServices(
        db=db,
        background_tasks=background_tasks,
        request=request_info,
        authorization=authorization
    )

    return donation_service.organization_request(payload=request)




# ==============================================================================
@donation_router.post("/remove-organization")
async def organization_remove_request(
    request: DonationOrgRemoveRequest,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    request_info: Request = None,
    authorization: str = Header(None)
):
    donation_service = DonationServices(
        db=db,
        background_tasks=background_tasks,
        request=request_info,
        authorization=authorization
    )
    return donation_service.organization_remove_request(payload=request)




# ==============================================================================
@donation_router.put("/organization-edit/{organization_id}")
async def edit_organization(
    organization_id: int,
    payload: DonationOrgRequest,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    request_info: Request = None,
    authorization: str = Header(None)
):
    donation_service = DonationServices(
        db=db,
        background_tasks=background_tasks,
        request=request_info,
        authorization=authorization
    )
    return donation_service.edit_organization(organization_id=organization_id, payload=payload)
    




# ==============================================================================
# ==============================================================================
