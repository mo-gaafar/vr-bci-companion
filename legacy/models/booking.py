from enum import Enum
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from models.common import CommonModel, PaginationIn, PaginationOut, Currency
from models.owner import OwnerOut, ProfileOutPublic


class BookingStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    rejected = "rejected"
    completed = "completed"


class UnitBookingType(str, Enum):
    one_day = "one_day"
    sunday_to_wednesday = "sunday_to_wednesday"
    thursday_to_saturday = "thursday_to_saturday"
    one_week = "one_week"
    one_month = "one_month"


class BookingInDB(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    unit_id: str = None
    owner_id: str = None
    customer_id: str = None
    booking_date: datetime = datetime.utcnow()
    check_in_date: datetime
    check_out_date: datetime
    price: float = 0.0
    currency: Currency = Currency.kwd
    booking_type: UnitBookingType = UnitBookingType.one_day
    status: BookingStatus = BookingStatus.pending

    # payment_info: Optional[PaymentInfo] = None




class BookingOutPublic(BaseModel):
    check_in_date: datetime
    check_out_date: datetime


class BookingOutOwner(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    booking_date: datetime
    check_in_date: datetime
    check_out_date: datetime
    price: float
    currency: Currency
    booking_type: UnitBookingType
    status: BookingStatus
    # payment_info: Optional[PaymentInfo] = None


class BookingOutOwnerDetailed(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    booking_date: datetime
    check_in_date: datetime
    check_out_date: datetime
    price: float
    currency: Currency
    booking_type: UnitBookingType
    status: BookingStatus
    # payment_info: Optional[PaymentInfo] = None
    customer: Optional[ProfileOutPublic] = None 
    


class BookingCreate(BaseModel):
    unit_id: str
    customer_id: str
    check_in_date: datetime
    check_out_date: datetime
    booking_type: UnitBookingType
    # payment_info: Optional[PaymentInfo] = None


class BookingSuccess(BaseModel):
    booking_id: str
    booking_date: datetime
    check_in_date: datetime
    check_out_date: datetime
    unit_id: str
    owner_id: str
    customer_id: str
    price: float
    currency: Currency
    # payment_info: Optional[PaymentInfo] = None


class UpdateBookingStatus(BaseModel):
    # booking_id: str
    status: BookingStatus
    # payment_info: Optional[PaymentInfo] = None