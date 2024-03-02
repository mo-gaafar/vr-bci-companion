from pydantic import BaseModel, Field

from datetime import datetime
from typing import Optional, List
from models.common import CommonModel, PaginationIn, PaginationOut, Currency
from enum import Enum
from models.units import UnitOutPublic, UnitOutAdmin
from models.booking import BookingOutPublic, UnitBookingType


class BookingOutNotification(BaseModel):
    id: str = Field(..., alias="_id")
    start_date: datetime
    end_date: datetime
    unit_out: UnitOutPublic
    booking_type: UnitBookingType
    name: str
    email: str
    phone: str


class ApprovalOutNotification(BaseModel):
    admin_comment: str
    unit_out: UnitOutPublic


class OwnerNotificationType(str, Enum):
    booking = "booking"
    approval = "approval"
    payment = "payment"


class OwnerNotification(BaseModel):
    title: str
    title_l1: str
    message: str
    message_l1: str
    timestamp: datetime = datetime.utcnow()
    read: bool = False
    type: OwnerNotificationType
    approval_out: Optional[ApprovalOutNotification] = None
    booking_out: Optional[BookingOutNotification] = None
