import os, dotenv
from decimal import Decimal

dotenv.load_dotenv()


class ENV:
    # Environment variables for email configuration
    EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = int(os.getenv("SMTP_PORT"))
    EMAIL_USE_TLS = bool(os.getenv("EMAIL_USE_TLS"))
    EMAIL_USE_SSL = bool(os.getenv("EMAIL_USE_SSL"))

    # Environment variables for SMS configuration
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

    # Secret Key for JWT
    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = os.getenv("ALGORITHM")
    ACCESS_EXPIRE = int(os.getenv("ACCESS_EXPIRE"))
    REFRESH_EXPIRE = int(os.getenv("REFRESH_EXPIRE"))

    # OTP
    OTP_TOKEN_EXPIRE_MIN = int(os.getenv("OTP_TOKEN_EXPIRE_MIN"))
    PASS_RST_TOKEN_EXPIRE = int(os.getenv("PASS_RST_TOKEN_EXPIRE_MIN"))


    # Rewards
    NEW_USER_REWARD_WITH_REFERRAL = Decimal(os.getenv("NEW_USER_REWARD_WITH_REFERRAL"))
    NEW_USER_REWARD_WITH_NO_REFERRAL = Decimal(os.getenv("NEW_USER_REWARD_WITH_NO_REFERRAL"))
    USER_REFERRAL_REWARD = Decimal(os.getenv("USER_REFERRAL_REWARD"))

    # Servece Charge
    SERVICE_CHARGE = Decimal(os.getenv("SERVICE_CHARGE"))

    # Server Version
    VERSION = os.getenv("VERSION")
    DEBUG = bool(os.getenv("DEBUG"))

    # Cloudinary Config
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")  
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

    SALT = os.getenv("SALT")

    SERVICE_ACCOUNT_PATH = os.getenv("SERVICE_ACCOUNT_PATH")







# if __name__ == "__main__":
#     print(ENV.EMAIL_USE_TLS)
#     print(ENV.EMAIL_USE_SSL)