
from pydantic import BaseModel, Field, validator, EmailStr
from pydantic.generics import GenericModel
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from typing import Optional, TypeVar, Generic, List
from enum import Enum
import uuid
from models.common import CommonModel, ObjId
from models.users import UserIn, UserOut, RoleEnum


class OwnerContact(BaseModel):
    name: str
    email: EmailStr
    phone: str  # TODO validate phone number format
    profile_pic: Optional[str] = None  # TODO validate url format


class Owner(BaseModel):
    # role: RoleEnum = RoleEnum.owner
    contact: OwnerContact


class OwnerInDB(Owner):
    id: Optional[str] = Field(None, alias="_id")
    auth_user_id: Optional[str] = None
    subscription_id: Optional[str] = None
    subscription_end_date: Optional[datetime] = None
    owned_unit_ids: Optional[List[str]] = []


class OwnerProfile(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    contact: OwnerContact
    units: List[str] = []  # TODO validate unit model


class OwnerCreate(BaseModel):
    contact: OwnerContact
    auth_user: UserIn


class OwnerOut(Owner):
    id: Optional[str] = Field(None, alias="_id")
    auth_user: UserOut
    subscription_end_date: Optional[datetime] = None


class ProfileOutPublic(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    name: str
    email: str
    phone: str
    profile_pic: Optional[str] = None


    