from fastapi import FastAPI, Header, Request, HTTPException, status
from pathlib import Path
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.constants import ENV
from admin.router.auth_router import admin_auth_router
from admin.router.access_router import admin_access_router

from app.schema.global_schema import GlobalResponse

from app.router.auth_router import auth_router
from app.router.wallet_router import wallet_router
from app.router.recharge_router import recharge_router
from app.router.bill_router import bill_router
from app.router.user_router import user_router
from app.router.qr_router import qr_router
from app.router.notify_router import notyfy_router
from app.router.history_router import history_router
from app.router.donation_router import donation_router
from app.router.country_router import country_router

from app.utils import Helpers, Token, Hashing




# create api
app = FastAPI(
    title="PocketPay API",
    description="A complete digital wallet and payment solution",
    version=ENV.VERSION,
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
TMP_DIR = Path("uploads/tmp")





# Custom exception handlers
# @app.exception_handler(404)
# async def custom_404_handler(request: Request, exc: HTTPException):
#     message = exc.detail if getattr(exc, "detail", None) else "Not Found"

#     return JSONResponse(
#         status_code=404,
#         content={
#             "success": False,
#             "error": "Not Found",
#             "message": message
#         }
#     )


# Custom exception handlers
# @app.exception_handler(Exception)
# async def server_exception_handler(request: Request, exc: Exception):
#     return JSONResponse(
#         status_code=500,
#         content={
#             "success": False,
#             "error": "Internal Server Error",
#             "message": "",
#         }
#     )



# ==============================================================================
# ==============================================================================

@app.get("/")
async def root(
    request: Request,
    authorization: str = Header(None)
):
    # Helpers.authorization(authorization)
    # print(Hashing.create_hash("1s22s22p6"))
    return {
        "message": "PocketPay API",
        "version": "1.0"
    }


@app.get("/offer")
async def offer(authorization: str = Header(None)):
    access_token = Helpers.authorization(authorization)

    token = Token()
    token.decode_token(access_token)

    return GlobalResponse(
        success=True,
        message="Current Offre",
        data={
            "offer": [
                {
                    "image_url": "https://res.cloudinary.com/dgh76k5vn/image/upload/v1772775093/rgvls7fslpabfgsrdlnw.jpg",
                    "title": "Big Cashback Offer!",
                    "description": f"Get up to 20% cashback on your first bill pay."
                },
                {
                    "image_url": "https://res.cloudinary.com/dgh76k5vn/image/upload/v1770636025/special-offer-red-label-illustration-free-vector_eq6bfq.jpg",
                    "title": "Mobile Recharge Deal",
                    "description": "Recharge 100 TK and get 10 TK instant cashback."
                },
                {
                    "image_url": "https://res.cloudinary.com/dgh76k5vn/image/upload/v1772775603/qg08lllvicvg8rnpsvui.jpg",
                    "title": "Refer and Earn",
                    "description": "Invite your friends and earn 50 TK for each referral."
                }
            ]
        }
    )


# Serve admin login page
@app.get("/terms-and-conditions")
async def terms_and_conditions():
    return templates.TemplateResponse("terms_and_conditions.html", {"request": {}})


@app.get("/admin")
async def admin_dashboard():
    return RedirectResponse("/admin/dashboard")


# Serve admin login page
@app.get("/admin/login")
async def admin_login():
    return templates.TemplateResponse("login.html", {"request": {}})



@app.get("/admin/dashboard")
async def admin_dashboard(request: Request):
    # Check if admin is logged in via cookie or token
    access_token = request.cookies.get("admin_access_token")

    if not access_token:
        # Redirect to login page if not authenticated
        return RedirectResponse("/admin/login")

    # Add token to headers for API calls
    request.headers.__dict__["_list"].append(
        (b"authorization", f"Bearer {access_token}".encode())
    )

    # Render dashboard template
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/admin/users")
async def admin_users(request: Request):
    # Check if admin is logged in via cookie or token
    access_token = request.cookies.get("admin_access_token")

    if not access_token:
        # Redirect to login page if not authenticated
        return RedirectResponse("/admin/login")

    # Add token to headers for API calls
    request.headers.__dict__["_list"].append(
        (b"authorization", f"Bearer {access_token}".encode())
    )

    # Render users template
    return templates.TemplateResponse("users.html", {"request": request})


@app.get("/admin/transactions")
async def admin_transactions(request: Request):
    # Check if admin is logged in via cookie or token
    access_token = request.cookies.get("admin_access_token")

    if not access_token:
        # Redirect to login page if not authenticated
        return RedirectResponse("/admin/login")

    # Add token to headers for API calls
    request.headers.__dict__["_list"].append(
        (b"authorization", f"Bearer {access_token}".encode())
    )

    # Render transactions template
    return templates.TemplateResponse("transactions.html", {"request": request})


@app.get("/admin/wallets")
async def admin_wallets(request: Request):
    # Check if admin is logged in via cookie or token
    access_token = request.cookies.get("admin_access_token")

    if not access_token:
        # Redirect to login page if not authenticated
        return RedirectResponse("/admin/login")

    # Add token to headers for API calls
    request.headers.__dict__["_list"].append(
        (b"authorization", f"Bearer {access_token}".encode())
    )

    # Render wallets template
    return templates.TemplateResponse("wallets.html", {"request": request})


@app.get("/admin/donations/create")
async def admin_donation_create(request: Request):
    # Check if admin is logged in via cookie or token
    access_token = request.cookies.get("admin_access_token")

    if not access_token:
        # Redirect to login page if not authenticated
        return RedirectResponse("/admin/login")

    # Render donation create template
    return templates.TemplateResponse("donation_manager.html", {"request": request})

@app.get("/admin/countries")
async def admin_countries(request: Request):
    # Check if admin is logged in via cookie or token
    access_token = request.cookies.get("admin_access_token")

    if not access_token:
        # Redirect to login page if not authenticated
        return RedirectResponse("/admin/login")

    # Add token to headers for API calls
    request.headers.__dict__["_list"].append(
        (b"authorization", f"Bearer {access_token}".encode())
    )

    return templates.TemplateResponse("country_manage.html", {"request": request})

@app.get("/admin/bill-providers")
async def admin_bill_providers(request: Request):
    # Check if admin is logged in via cookie or token
    access_token = request.cookies.get("admin_access_token")

    if not access_token:
        # Redirect to login page if not authenticated
        return RedirectResponse("/admin/login")

    # Add token to headers for API calls
    request.headers.__dict__["_list"].append(
        (b"authorization", f"Bearer {access_token}".encode())
    )

    # Render bill providers template
    return templates.TemplateResponse("bill_provider.html", {"request": request})

@app.get("/admin/mobile-operators")
async def admin_mobile_operators(request: Request):
    # Check if admin is logged in via cookie or token
    access_token = request.cookies.get("admin_access_token")

    if not access_token:
        # Redirect to login page if not authenticated
        return RedirectResponse("/admin/login")

    # Add token to headers for API calls
    request.headers.__dict__["_list"].append(
        (b"authorization", f"Bearer {access_token}".encode())
    )

    # Render mobile operators template
    return templates.TemplateResponse("mobile_operators.html", {"request": request})

@app.get("/admin/profile")
async def admin_profile(request: Request):
    # Check if admin is logged in via cookie or token
    access_token = request.cookies.get("admin_access_token")

    if not access_token:
        # Redirect to login page if not authenticated
        return RedirectResponse("/admin/login")

    # Render profile template
    return templates.TemplateResponse("profile.html", {"request": request})


@app.get("/admin/admins/create")
async def admin_create(request: Request):
    # Check if admin is logged in via cookie or token
    access_token = request.cookies.get("admin_access_token")

    if not access_token:
        # Redirect to login page if not authenticated
        return RedirectResponse("/admin/login")

    # Render create admin template
    return templates.TemplateResponse("admin_create.html", {"request": request})


@app.get("/admin/create")
async def admin_create_legacy(request: Request):
    # Legacy GET route to avoid 405 when visiting /admin/create in browser
    return RedirectResponse("/admin/admins/create")





# Include routers
app.include_router(admin_access_router, prefix="/admin", tags=["Admin Management"]) # check
app.include_router(admin_auth_router, prefix="/admin", tags=["Admin Management"])   # check

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])            # check
app.include_router(wallet_router, prefix="/wallet", tags=["Wallet"])                # check
app.include_router(user_router, prefix="/user", tags=["User Data"])                 # check
app.include_router(recharge_router, prefix="/recharge", tags=["Mobile Recharge"])   # check
app.include_router(bill_router, prefix="/bill", tags=["Bill Payment"])              # check
app.include_router(qr_router, prefix="/qr", tags=["Mack QR"])                       # check
app.include_router(notyfy_router, prefix="/ws", tags=["Notifications"])             # check
app.include_router(history_router, prefix="/history", tags=["Transaction History"]) # check
app.include_router(donation_router, prefix="/donation", tags=["Donations"])         # check
app.include_router(country_router, prefix="/country", tags=["Countries"])           # check





# ==============================================================================
# ==============================================================================
