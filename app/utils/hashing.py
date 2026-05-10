from passlib.context import CryptContext

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Hashing:
    @staticmethod
    def create_hash(password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_otp(plain_otp: str, hashed_otp: str) -> bool:
        return pwd_context.verify(plain_otp.strip(), hashed_otp)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def verify_hash(plain_value: str, hashed_value: str) -> bool:
        """Verify a plain value against its hash (for token hashing)."""
        return pwd_context.verify(plain_value, hashed_value)


# if __name__ == "__main__":
#     print(Hashing.create_hash(""))