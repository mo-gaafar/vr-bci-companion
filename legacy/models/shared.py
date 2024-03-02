from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from models.common import CommonModel, PaginationIn, PaginationOut, Currency
from models.owner import OwnerOut
from auth.models import UserOut
from models.customer import CustomerOutPublic
from models.booking import BookingOutOwner


class UnitBookingOutOwner(BookingOutOwner):
    customer: CustomerOutPublic
