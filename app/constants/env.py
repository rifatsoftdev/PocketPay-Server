import os, dotenv
from decimal import Decimal

dotenv.load_dotenv()


class ENV:
    # DataBase configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    
    # # Email configuration
    EMAIL_ADDRESS: str = os.getenv("EMAIL_ADDRESS")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD")
    SMTP_SERVER: str = os.getenv("SMTP_SERVER")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT"))
    EMAIL_USE_TLS: bool = bool(os.getenv("EMAIL_USE_TLS"))
    EMAIL_USE_SSL: bool = bool(os.getenv("EMAIL_USE_SSL"))

    # JWT configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM")
    ACCESS_EXPIRE: int = int(os.getenv("ACCESS_EXPIRE"))
    REFRESH_EXPIRE: int = int(os.getenv("REFRESH_EXPIRE"))
    OTP_TOKEN_EXPIRE_MIN: int = int(os.getenv("OTP_TOKEN_EXPIRE_MIN"))
    PASS_RST_TOKEN_EXPIRE: int = int(os.getenv("PASS_RST_TOKEN_EXPIRE_MIN"))

    # Redis configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "memory://")

    # Rewards configuration
    NEW_USER_REWARD_WITH_REFERRAL: Decimal = Decimal(os.getenv("NEW_USER_REWARD_WITH_REFERRAL"))
    NEW_USER_REWARD_WITH_NO_REFERRAL: Decimal = Decimal(os.getenv("NEW_USER_REWARD_WITH_NO_REFERRAL"))
    USER_REFERRAL_REWARD: Decimal = Decimal(os.getenv("USER_REFERRAL_REWARD"))

    # Service Charge configuration
    SERVICE_CHARGE: Decimal = Decimal(os.getenv("SERVICE_CHARGE"))

    # Server Version and Debug mode
    VERSION: str = os.getenv("VERSION")
    DEBUG: bool = bool(os.getenv("DEBUG"))

    # Cloudinary configuration
    CLOUDINARY_CLOUD_NAME: str = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY")  
    CLOUDINARY_API_SECRET: str = os.getenv("CLOUDINARY_API_SECRET")

    # Salt for password hashing
    SALT: str = os.getenv("SALT")

    # Salt for password hashing
    POCKETPAY_ADMINSDK: str = os.getenv("POCKETPAY_ADMINSDK")
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID")

    # CORS configuration
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS")

    # Logging configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL")

    # Default admin
    DEFAULT_ADMIN_EMAIL: str = os.getenv("DEFAULT_ADMIN_EMAIL")
    DEFAULT_ADMIN_PHONE: str = os.getenv("DEFAULT_ADMIN_PHONE")
    DEFAULT_ADMIN_PASSWORD: str = os.getenv("DEFAULT_ADMIN_PASSWORD")
    DEFAULT_ADMIN_NAME: str = os.getenv("DEFAULT_ADMIN_NAME")
    
    # Default user
    DEFAULT_USER_EMAIL: str = os.getenv("DEFAULT_USER_EMAIL")
    DEFAULT_USER_PHONE: str = os.getenv("DEFAULT_USER_PHONE")
    DEFAULT_USER_PASSWORD: str = os.getenv("DEFAULT_USER_PASSWORD")
    DEFAULT_USER_NAME: str = os.getenv("DEFAULT_USER_NAME")





    # SERVICE_ACCOUNT_PATH = os.getenv("SERVICE_ACCOUNT_PATH")
    # GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")



# if __name__ == "__main__":
#     print(ENV.EMAIL_USE_TLS)
#     print(ENV.EMAIL_USE_SSL)