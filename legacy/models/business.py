from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Annotated
from fastapi import Header, HTTPException, Form, UploadFile
from datetime import datetime
from models.common import ObjId
# from models.messaging import 

FEATURES = ["amenities", "guest_list_filters", "scans_histogram",
            "guest_history", "recent_scans", "scan_logs", "analytics"]


class BusinessPreLogin(BaseModel):
    name: str
    logo_link: Optional[str] = Field(None)


class Business(BaseModel):
    id: str = Field(None, alias="_id")
    tenant_id: str
    name: str
    email: EmailStr
    phone: str

    payment_merchant_id: Optional[str] = Field(None)
    payment_secret: str = Field(None)
    payment_public: str = Field(None)
    payment_integration_id: Optional[str] = Field(None)
    payment_frame_id: Optional[str] = Field(None)
    payment_api_key: Optional[str] = Field(None)

    is_active: Optional[bool] = Field(True)
    subscription_id: str = Field(None)
    logo_link: Optional[str] = Field(None)


class BusinessForm(BaseModel):
    name: Annotated[str, Form(...)]
    email: Annotated[str, Form(...)]
    phone: Annotated[str, Form(...)]
    logo: Annotated[UploadFile, Form(...)]
    payment_secret: Annotated[str, Form(...)]
    payment_public: Annotated[str, Form(...)]
    payment_integration_id: Annotated[str, Form(...)]
    subscription_end: Annotated[datetime, Form(...)]
    plan_name: Annotated[str, Form(...)]


class Subscription(BaseModel):
    id: str = Field(None, alias="_id")
    tenant_id: str = Field(None, alias="tenant_id")
    start_date: datetime
    end_date: datetime
    is_active: bool
    is_trial: bool
    plan_id: str = Field(None, alias="plan_id")
    plan_name: str

    # class Config:
    #     json_encoders = {
    #         ObjId: lambda v: str(v),
    #     }


class PlanIn(BaseModel):
    name: str
    price: int
    is_monthly: bool
    is_annual: bool
    description: Optional[str] = Field(None)
    features: Optional[List[str]] = Field(None)


class Plan(PlanIn):
    id: str = Field(..., alias="_id")


class ScheduleItem(BaseModel):
    day_of_week: str
    opening_hr: str
    closing_hr: str


class Schedule(BaseModel):
    is_one_time: bool
    start_date: datetime
    end_date: datetime
    weekly_schedule: List[ScheduleItem] = Field(None)


class Venue(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    business_id: str
    name: str
    description: Optional[str] = Field(None)

    location: Optional[str] = Field(None)
    maps_link: Optional[str] = Field(None)
    thumbnail_link: Optional[str] = Field(None)

    parking_limit: int = 1000
    parking_used_slots: int = 0

    ticket_message: Optional[str] = Field(None)
    order_message: Optional[str] = Field(None)

    is_active: Optional[bool] = Field(True)
    opening_schedule: Optional[Schedule] = Field(None)


class BusinessDetails(Business):
    subscription_end: datetime
    plan_name: str
    plan_features: List[str]
    venues: Optional[List[Venue]] = Field(None)
