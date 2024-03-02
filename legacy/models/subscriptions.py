from auth.models import RoleEnum
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime
from models.owner import OwnerOut, Owner
from models.common import CommonModel


class PaymentMethod(str, Enum):
    card = "card"
    cash = "cash"
    bank_transfer = "bank_transfer"
    paypal = "paypal"


class PaymentStatus(str, Enum):
    pending = "pending"
    success = "success"
    failed = "failed"


class PaymentInfo(BaseModel):
    price: float
    currency: str
    payment_method: PaymentMethod = PaymentMethod.card
    # payment_status: PaymentStatus = PaymentStatus.pending
    payment_date: datetime


class SubscriptionStatus(str, Enum):
    active = "active"
    expired = "expired"
    cancelled = "cancelled"


class SubscriptionType(str, Enum):
    monthly = "monthly"
    quarterly = "quarterly"
    biyearly = "biyearly"
    yearly = "yearly"


class SubscriptionPlan(BaseModel):
    id: str = Field(..., alias="_id")
    type: SubscriptionType
    price: float
    currency: str
    description: str
    max_units: int = 1


class SubscriptionOut(BaseModel):
    id: str = Field(..., alias="_id")
    status: SubscriptionStatus  # derived from start_date and end_date
    subscription_type: SubscriptionType
    start_date: datetime
    end_date: datetime

class OwnerSubscription(BaseModel):
    id: str = Field(..., alias="_id")
    owner_id: str
    plan_id: str
    start_date: datetime
    end_date: datetime
    payment_info: Optional[PaymentInfo] = None
    max_units: Optional[int] = 1

class OwnerSubscriptionOut(BaseModel):
    id: str = Field(..., alias="_id")
    status: SubscriptionStatus  # derived from start_date and end_date
    subscription_type: SubscriptionType
    start_date: datetime
    end_date: datetime
    owner: Optional[OwnerOut] = None   # derived from owner_id
    max_units: Optional[int] = 1


class OwnerSubscriptionIn(BaseModel):
    type: SubscriptionType
    start_date: datetime
    end_date: datetime
    owner_id: str
    max_units: Optional[int] = 1


class SubscriptionInDB(CommonModel):
    id: Optional[str] = Field(None, alias="_id")
    subscriber_id: str
    subscriber_type: Optional[RoleEnum] = RoleEnum.owner
    subscription_type: SubscriptionType
    start_date: datetime
    end_date: datetime
    payment_info: Optional[PaymentInfo] = None
    max_units: Optional[int] = 1
