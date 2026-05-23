# app/core/rate_limiter.py

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.constants import ENV


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri=ENV.REDIS_URL,
    headers_enabled=True,
)