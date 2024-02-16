from enum import Enum
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from models.common import CommonModel
from config.config import pytz_timezone


class PaymentStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    refunded = "refunded"
    cancelled = "cancelled"
    failed = "failed"
    voided = "voided"


class PaymentMethod(str, Enum):
    cash = "cash"
    card = "card"
    
