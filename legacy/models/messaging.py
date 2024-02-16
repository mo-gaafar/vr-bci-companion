from pydantic import BaseModel, Field
from typing import Optional, List, Annotated
from enum import Enum


class MessageMedium(str, Enum):
    mail = "mail"
    landing = "landing"
    whatsapp = "whatsapp"
    sms = "sms"


class MessageTopic(str, Enum):
    order_confirmation = "order_confirmation"
    order_refund = "order_refund"

    ticket_confirmation = "ticket_confirmation"
    general_marketing = "general_marketing"
    user_password_reset = "user_password_reset"
    user_welcome = "user_welcome"
    user_verification = "user_verification"
    user_verification_otp = "user_verification_otp"

    ticket_item = "ticket_item"


class TemplateContent(BaseModel):
    plain_text: Optional[str] = Field(None)
    html_content: Optional[str] = Field(None)
    css_content: Optional[str] = Field(None)
    js_content: Optional[str] = Field(None)
    wa_template: Optional[str] = Field(None)


class Template(BaseModel):
    id: str = Field(None, alias="_id")
    name: str
    subject: Optional[str] = Field(None)
    medium: MessageMedium
    topic: MessageTopic
    content: TemplateContent
    is_active: bool = Field(True)
