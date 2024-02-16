from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from models.common import CommonModel


class Customer(CommonModel):
    id: Optional[str] = Field(None, alias="_id")
    name: str
    email: EmailStr
    phone: str
    is_active: Optional[bool] = Field(True)
    ticket_ids: Optional[List[str]] = Field(default_factory=list)
    order_ids: Optional[List[str]] = Field(default_factory=list)


class OrderCustomer(CommonModel):
    id: Optional[str] = Field(None, alias="_id")
    name: str
    email: Optional[EmailStr]
    phone: Optional[str]

    @validator('name')
    def validate_two_words(cls, value):
        words = value.split(" ")
        if len(words) < 2:
            raise ValueError('Two words are required, first and last name')
        return value
