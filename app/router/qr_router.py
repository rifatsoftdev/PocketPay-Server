import qrcode, io

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.constants.colors import AnsiColor
from app.constants.string import String
from app.schema.qr_schema import QRRequest



qr_router = APIRouter()

ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"]
MAX_SIZE = 5 * 1024 * 1024  # 5MB


"""
QRTYPE
self, paybill, donation, sendmoney, recharge
"""


# ==============================================================================
"""
QR Code mack

request example
post {
    "qr_type": "self",
    "full_name": "David",
    "phone_number": "+8801812345677",
    "email_address": "david@gmail.com",
    "amount": 100,
    "currency": "BDT"
}

response example

"""
# ==============================================================================

@qr_router.post("/generate-qr")
async def generate_qr_api(request: QRRequest):
    try:
        data_str = request.model_dump_json()

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )

        qr.add_data(data_str)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        return StreamingResponse(
            buf,
            media_type="image/png",
            headers={"Content-Disposition": "inline; filename=qr.png"}
        )

    except HTTPException:
        raise

    except Exception as e:
        print(f"{AnsiColor.RED}INFO{AnsiColor.RED}:     {e}")
        raise HTTPException(status_code=500, detail="QR generation failed")





# ==============================================================================
# ==============================================================================