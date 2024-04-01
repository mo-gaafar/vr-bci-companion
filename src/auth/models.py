from bson import ObjectId
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, validator
from common.models import CommonModel
from typing import Optional, List, Annotated
from common.models import ObjectIdPydanticAnnotation, MongoBaseModel
# from common.models import PyObjectId as ObjId

from enum import Enum

from pydantic import BaseModel


class GenerateOTPResponse(BaseModel):
    otp: str
    pairing_id: Annotated[ObjectId, ObjectIdPydanticAnnotation]
    expiry: int


class RoleEnum(str, Enum):
    admin = "admin"
    owner = "owner"
    guest = "guest"
    patient = "patient"
    doctor = "doctor"
    nurse = "nurse"


class BaseUser(MongoBaseModel):
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


class UserInDB(BaseUser):
    # id: Annotated[ObjectId, ObjectIdPydanticAnnotation]
    encrypted_pass: str = Field("None")
    valid_date: Optional[datetime] = None  # logs out users before this date
    device_id: Optional[str] = None


class UserOut(CommonModel):
    id: Optional[str] = Field(None, alias="_id")
    username: str
    role: RoleEnum = Field(RoleEnum.guest)
    device_id: Optional[str] = None


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


class PairingCodeRecord(MongoBaseModel):
    user_id: Optional[Annotated[ObjectId, ObjectIdPydanticAnnotation]] = None
    device_id: str
    code: str
    generation_timestamp: datetime
    expiration_timestamp: datetime
