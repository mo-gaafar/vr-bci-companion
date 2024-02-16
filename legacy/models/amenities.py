from models.customer import OrderCustomer
from models.common import CommonModel
from models.payment import PaymentMethod, PaymentStatus
from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import Field
from models.common import CheckInHistory, short_uuid


class AmenityType(str, Enum):
    parking = "parking"
    drink = "drink"
    food = "food"
    other = "other"


class Amenity(CommonModel):

    name: str
    type: AmenityType
    quantity_allowed: int
    quantity_used: int = 0
    # if used exceed allowed then price is charged
    description: Optional[str] = Field(None)
    unit_price: Optional[int] = Field(0)


class CheckInCar(CheckInHistory):
    plate_number: Optional[str] = None
    # plate_image_url: str = Field(None)
    # parked_location: str = Field(None)
    # car_brand: str = Field(None)
    # car_model: str = Field(None)
    # car_color: str = Field(None)


class ParkingAmenity(Amenity):
    name: str = "Parking"
    type: AmenityType = Field(AmenityType.parking)
    quantity_allowed: int = 1
    scan_history: Optional[List[CheckInCar]] = Field(default_factory=list)


class ParkingScanOut(CommonModel):
    guest_details: OrderCustomer
    parking_amenity: ParkingAmenity
    entry_time: Optional[datetime] = Field(default_factory=datetime.utcnow)
    exit_time: Optional[datetime] = Field(None)
    duration_min: int = 0
    plate_number: str = "N/A"
    entry_price: int = 0
    remaning_spaces: int = 0
    remaining_parking_uses: int = 0
    message: str = ""


class FoodstuffAmenity(Amenity):
    id: Optional[str] = Field(default_factory=short_uuid)
    type: AmenityType = Field(AmenityType.drink)
    image_url: str = 'https://i0.wp.com/johnsonwebbert.com/wp-content/uploads/2015/03/Fork__knife.svg_.png?ssl=1'
    scan_history: Optional[List[CheckInHistory]] = Field(default_factory=list)


class FoodstuffScanOut(CommonModel):
    guest_details: OrderCustomer
    selected_food: Optional[FoodstuffAmenity] = Field(None)
    remaining_uses: int = 0
    amenities_list: list[FoodstuffAmenity]
    allowed_foodstuff: list[FoodstuffAmenity]
    message: str = ""


def default_foodstuff():
    return [FoodstuffAmenity(name="Drink", quantity_allowed=1, unit_price=0, type=AmenityType.drink, description="A free drink of your choice!")]


class Amenities(CommonModel):
    parking: Optional[ParkingAmenity] = Field(default_factory=ParkingAmenity)
    foodstuff: Optional[List[FoodstuffAmenity]] = Field(
        default_factory=default_foodstuff)

# class ParkingInfo(CommonModel):
#     parking_allowed: bool = False
#     parking_price: int = 0


class VenueParkingSummary(CommonModel):
    total_parked_cars: int
    max_parking_capacity: int
    remaining_parking_capacity: int
    total_parking_durartion_min: int
    average_parking_duration_min: int
