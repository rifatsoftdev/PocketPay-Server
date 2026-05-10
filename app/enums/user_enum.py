from enum import Enum



# User Status
class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"
    PENDING = "pending"


# User Gender
class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNDIFINED = "undefined"


# Uaer type
class UserType(str, Enum):
    NORMAL = "normal"
    AGENT = "agent"