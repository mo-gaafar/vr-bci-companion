from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, validator
from models import CommonModel
from typing import Optional, List
from models import ObjId
from enum import Enum

from pydantic import BaseModel


class GenerateOTPResponse(BaseModel):
    otp: str
    expiry: int


class RoleEnum(str, Enum):
    admin = "admin"
    owner = "owner"
    guest = "guest"


class BaseUser(CommonModel):
    # id: str = Field(..., alias="_id")
    username: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_active: bool = Field(True)
    role: RoleEnum = Field(RoleEnum.guest)

    # validate if either email or phone is provided
    @validator("email")
    def email_or_phone_required(cls, v, values, **kwargs):
        if v is None and values.get("phone") is None:
            raise ValueError("Either email or phone must be provided")
        return v

    # current_subscription: Field(None, alias="subscription_id")
    # logo_link: str
    # business_id: str
    # customer_id: str


class UserInDB(BaseUser):
    id: Optional[str] = Field(None, alias="_id")
    encrypted_pass: str = Field("None")
    valid_date: Optional[datetime] = None  # logs out users before this date

    class Config:
        json_encoders = {
            ObjId: lambda v: str(v),
        }


class UserOut(CommonModel):
    id: Optional[str] = Field(None, alias="_id")
    username: str
    role: RoleEnum = Field(RoleEnum.guest)


class UserToken(CommonModel):
    auth_token: Optional[str] = Field(None)
    refresh_token: Optional[str] = Field(None)


class UserIn(BaseUser):
    password: str


class AdminInDB(CommonModel):
    id: Optional[str] = Field(None, alias="_id")
    auth_user_id: str
    audit_logs: List[dict] = []
    login_history: List[dict] = []
    date_created: datetime = Field(datetime.utcnow())
