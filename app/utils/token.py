from datetime import datetime, timedelta
from jose import JWTError, jwt
import os, dotenv

dotenv.load_dotenv()



class Token:
    def __init__(self):
        self.SECRET_KEY = os.getenv("SECRET_KEY", "mysecretkey")
        self.ALGORITHM = os.getenv("ALGORITHM", "HS256")

        self.ACCESS_EXPIRE = int(os.getenv("ACCESS_TOKEN_EXPIRE", 30))            # minutes
        self.REFRESH_EXPIRE = int(os.getenv("REFRESH_EXPIRE", 30))                # days
        self.OTP_TOKEN_EXPIRE = int(os.getenv("OTP_TOKEN_EXPIRE_MIN", 5))         # minutes
        self.PASS_RST_TOKEN_EXPIRE = int(os.getenv("PASS_RST_TOKEN_EXPIRE", 10))  # minutes


    # ---------- CREATE TOKENS ----------

    def create_access_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.ACCESS_EXPIRE)
        to_encode.update({
            "exp": expire,
            "type": "access"
        })
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def create_refresh_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.REFRESH_EXPIRE)
        to_encode.update({
            "exp": expire,
            "type": "refresh"
        })
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def create_otp_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.OTP_TOKEN_EXPIRE)
        to_encode.update({
            "exp": expire,
            "type": "otp"
        })
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def create_pass_rst_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.PASS_RST_TOKEN_EXPIRE)
        to_encode.update({
            "exp": expire,
            "type": "otp"
        })
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)


    # ---------- DECODE / VERIFY ----------
    def decode_token(self, token: str):
        try:
            payload = jwt.decode(
                token,
                self.SECRET_KEY,
                algorithms=[self.ALGORITHM]
            )
            return payload
        except JWTError:
            return None