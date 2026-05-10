from fastapi import APIRouter, Depends, BackgroundTasks, Request, Header
from sqlalchemy.orm import Session

from app.core.database import get_db

# from app.enums import NotificationType
from app.schema import GlobalResponse, NewCountryRequest, DisableCountryRequest
from app.services import CountryService


country_router = APIRouter()


# ==============================================================================
"""
Get all supported countries

request example
get /country/counties

response example
{
    "success": true,
    "message": "Supported Countries",
    "data": {
        "countries": [
            {
                "counrty_id": "country_id",
                "counrty_name": "Bangladesh",
                "counrty_code": "+880",
                "flag_emoji": "🇧🇩",
                "currency": "BDT",
                "currency_symbol": "৳"
            }
        ]
    }
}
"""

# ==============================================================================

@country_router.get("/counties")
async def get_counties(
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    countryService = CountryService(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return countryService.get_active_countries()




# ==============================================================================
"""
Add new country

request example
post 
{
    "user_id": "user_id",
    "access_token": "access_token",
    "android_id": "android_id",
    "android_uuid": "android_uuid",
    "user_password": "password",

    "counrty_name": "name",
    "counrty_code": "code",
    "flag_emoji": "flag_emoji",
    "currency": "currency",
    "currency_symbol": "currency_symbol"
}

response example
{
    "success": true,
    "message": "Country Added Successfully",
    "data": {
        "country_id": "country_id",
        "country_name": "country_name",
        "country_code": "country_code",
        "flag_emoji": "flag_emoji",
        "currency": "currency",
        "currency_symbol": "currency_symbol"
    }
}
"""
# ==============================================================================

@country_router.post("/add-new-country")
async def new_country(
    request: Request,
    payload: NewCountryRequest,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    countryService = CountryService(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return countryService.add_new_country(payload=payload)


@country_router.put("/country-edit/{country_id}")
async def edit_country(
    country_id: str,
    request: Request,
    payload: NewCountryRequest,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    countryService = CountryService(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return countryService.edit_country(country_id=country_id, payload=payload)




# ==============================================================================
"""
Disable country

request example
post 
{
    "user_id": "user_id",
    "android_id": "android_id",
    "android_uuid": "android_uuid",
    "user_password": "password",
    "counrty_id": "counrty_id"
}

response example
{
    "success": true,
    "message": "Country Added Successfully",
    "data": {
        
    }
}
"""
# ==============================================================================

@country_router.post("/inactive-country")
async def inactive_country(
    request: Request,
    payload: DisableCountryRequest,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    countryService = CountryService(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return countryService.inactive_country(payload=payload)




# ==============================================================================
"""
active country

request example
post 
{
    "user_id": "user_id",
    "android_id": "android_id",
    "android_uuid": "android_uuid",
    "user_password": "password",
    "counrty_id": "counrty_id"
}

response example
{
    "success": true,
    "message": "Country Added Successfully",
    "data": {
        
    }
}
"""
# ==============================================================================

@country_router.post("/active-country")
async def active_country(
    request: Request,
    payload: DisableCountryRequest,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    countryService = CountryService(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return countryService.active_country(payload=payload)




# ==============================================================================
# ==============================================================================
