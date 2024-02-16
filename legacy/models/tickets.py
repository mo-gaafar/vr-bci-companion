from models.common import CommonModel, CheckInHistory
from models.amenities import Amenities
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from models.customer import OrderCustomer
from models.common import CommonModel
from models.payment import PaymentMethod, PaymentStatus
from datetime import datetime
from config.config import pytz_timezone
from enum import Enum


class TicketTier(CommonModel):
    id: Optional[str] = Field(None, alias="_id")
    name: str = Field(...)
    price: int
    max_quantity: Optional[int] = Field(99999)
    quantity_sold: int = 0
    description: Optional[str] = Field(None)
    amenities: Optional[Amenities] = Field(default_factory=Amenities)
    venue_id: str = ''
    enabled: bool = True


class Ticket(CommonModel):
    id: Optional[str] = Field(None, alias="_id")
    order_id: str
    venue_id: str

    tier_id: str
    tier_name: str
    price: int

    payment_method: Optional[PaymentMethod] = Field("cash")
    is_valid: Optional[bool] = Field(False)

    guest_details: OrderCustomer

    date_start: Optional[datetime] = Field(None)
    date_expire: Optional[datetime] = Field(None)

    date_created: datetime = Field(default_factory=datetime.utcnow)
    is_active: Optional[bool] = Field(False)
    message_sent: Optional[bool] = Field(False)
    check_in: Optional[datetime] = Field(None)
    check_out: Optional[datetime] = Field(None)
    check_history: Optional[List[CheckInHistory]] = Field(default_factory=list)
    amenities: Optional[Amenities] = Field(
        Amenities(parking=None, foodstuff=None))


class TicketDisplay(CommonModel):
    ticket_id: str
    ticket_tier_name: str
    ticket_tier_price: int
    customer: OrderCustomer
    payment_method: Optional[PaymentMethod] = Field("cash")
    date_start: Optional[datetime] = Field(None)
    iframe_url: Optional[str] = Field(None)


class TicketsSummaryStatus(CommonModel):
    checked_in: int
    checked_out: int
    total_bought_for_today: int
    total_bought_revenue_for_today: int
    total_bought_today: int
    total_bought_revenue_today: int
    total_inside: int
    total_left: int


class GuestInList(CommonModel):
    name: str
    ticket_id: str
    status_message: str
    is_active: bool
    payment_method: PaymentMethod
    ticket_tier_name: str
    last_check: datetime = Field(None)


class ScanOut(CommonModel):
    guest_info: OrderCustomer
    is_active: bool
    tier_name: str
    message: str


class GuestTicketDetails(CommonModel):
    name: str
    email: EmailStr
    phone: str

    ticket_id: str
    order_id: str
    status_message: str
    is_active: bool
    payment_method: str
    ticket_tier_name: str
    check_in: datetime = Field(None)
    check_out: datetime = Field(None)
    last_check: Optional[datetime] = Field(None)
    check_history: Optional[list[CheckInHistory]] = Field(default_factory=list)
    amenities: Optional[Amenities] = Field(None)
