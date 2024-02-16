from pydantic import BaseModel, Field
from typing import List, Optional
from models.tickets import TicketTier, Ticket
from models.customer import Customer, OrderCustomer
from models.payment import PaymentMethod, PaymentStatus
from models.common import CommonModel
from datetime import datetime
from config.config import pytz_timezone
from enum import Enum

from datetime import timedelta


class OrderItem(CommonModel):
    ticket_tier_id: str
    ticket_tier_name: str
    ticket_tier_price: Optional[int] = Field(0)
    date_start: Optional[datetime] = datetime.utcnow()
    date_expire: Optional[datetime] = None
    customer: OrderCustomer
    ticket_id: Optional[str] = Field(None)
    # quantity: int


class OrderPayment(CommonModel):
    transaction_id: Optional[str] = Field(None)
    method: Optional[PaymentMethod] = Field("cash")
    total_amount: int
    currency: Optional[str] = Field("EGP")
    date_started: Optional[datetime] = Field(datetime.utcnow())
    date_completed: Optional[datetime] = Field(None)
    status: Optional[PaymentStatus] = Field(PaymentStatus.pending)
    # enum for status


class Order(CommonModel):
    id: Optional[str] = Field(None, alias="_id")
    buyer: OrderCustomer
    venue_id: Optional[str] = Field(None)
    order_items: List[OrderItem]  # ticket_tier, quantity
    payment_data: OrderPayment
    date_created: Optional[datetime] = Field(default_factory=datetime.utcnow)
    message_sent: Optional[bool] = Field(False)


class OrderOut(CommonModel):
    id: Optional[str] = Field(None, alias="_id")
    buyer: OrderCustomer
    venue_id: Optional[str] = Field(None)
    order_items: List[OrderItem]  # ticket_tier, quantity


class OrderCheckoutIn(CommonModel):
    buyer: OrderCustomer
    venue_id: str
    order_items: List[OrderItem]
    payment_method: Optional[PaymentMethod] = Field("cash")
    promocode: Optional[str] = Field(None)


class OrderCheckoutOut(CommonModel):
    order_id: str
    payment_url: Optional[str] = Field(None)
    payment_method: PaymentMethod
    status: str
