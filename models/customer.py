from models.common import CommonModel, PaginationIn, PaginationOut, Currency
from fastapi import APIRouter, Depends, HTTPException, Header, Query, Path
from pydantic import EmailStr, Field
from typing import Optional


class CustomerForm(CommonModel):
    first_name: str
    last_name: str

    email: Optional[EmailStr] = None
    phone: str  # TODO validate phone number format
    # password: str
    # profile_pic: Optional[str] = None  # TODO validate url format
    # booking_history: Optional[list[str]] = []
    # wishlist: Optional[list[str]] = []


class CustomerSignupSuccess(CommonModel):
    customer_id: str
    # auth_user_id: str


class CustomerSinupIn(CustomerForm):
    password: str


class CustomerOutPublic(CommonModel):
    id: Optional[str] = Field(None, alias="_id")
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    # profile_pic: Optional[str] = None


class CustomerInDB(CustomerForm):
    id: Optional[str] = Field(None, alias="_id")
    # role: RoleEnum = RoleEnum.customer
    auth_user_id: Optional[str] = None
