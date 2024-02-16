from models.owner import ProfileOutPublic
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime
from models.common import CommonModel, PaginationIn, PaginationOut, Currency
from models.owner import OwnerOut, ProfileOutPublic
from models.booking import BookingInDB, BookingOutPublic, UnitBookingType, BookingSuccess


class UnitPricing(BaseModel):
    price: float
    currency: Currency = Currency.kwd
    pricing_type: UnitBookingType


class UnitType(str, Enum):
    chalet = "chalet"
    farm = "farm"
    rest_house = "rest_house"


class UnitAmenities(BaseModel):
    #! make sure these are optional parameters
    pool: Optional[bool] = False
    gym: Optional[bool] = False
    parking: Optional[bool] = False
    security: Optional[bool] = False
    wifi: Optional[bool] = False
    ac: Optional[bool] = False
    heating: Optional[bool] = False
    kitchen_utensils: Optional[bool] = False
    levels: Optional[int] = 1
    
    num_master_bedrooms: Optional[int] = 0
    num_single_bedrooms: Optional[int] = 0
    num_bathrooms: Optional[int] = 0 

    # num_bedrooms: Optional[int] = 0 # new
    num_living_rooms: Optional[int] = 0

    num_public_pools: Optional[int] = 0
    num_private_pools: Optional[int] = 0
    garden: Optional[bool] = False
    elevator: Optional[bool] = False
    driver_room: Optional[bool] = False
    nanny_room: Optional[bool] = False
    sea_nearby: Optional[bool] = False
    elderly_disabled_suitable: Optional[bool] = False


class LocationLevel(str, Enum):
    address = "address"
    area = "area"
    city = "city"
    country = "country"


class LocationItem(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    name: str
    name_l1: str
    level: LocationLevel = LocationLevel.city
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class UnitLocation(BaseModel):
    address: list[LocationItem]

    latitude: float
    longitude: float


class UnitBase(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    owner_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    location: UnitLocation
    type: UnitType = UnitType.chalet


class ApprovalStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    suspended = "suspended"


class ApprovalType(str, Enum):
    creation = "creation"
    update = "update"
    deletion = "deletion"


class UnitApproval(BaseModel):
    unit_id: Optional[str] = None
    admin_id: Optional[str] = None

    approval_type: ApprovalType = ApprovalType.creation
    approval_status: ApprovalStatus = ApprovalStatus.pending
    admin_review: Optional[str] = None

    time_created: Optional[datetime] = None
    time_updated: Optional[datetime] = None


class UnitCreate(UnitBase):
    amenities: UnitAmenities
    pricing_list: list[UnitPricing]


class BlockedDate(BaseModel):
    recurring_times: int = 0
    interval_days: Optional[int] = None
    start_date: datetime
    end_date: datetime


class GalleryType(str, Enum):
    image = "image"
    video = "video"


class GalleryItem(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    order: int
    url: str
    type: GalleryType
    alt_text: Optional[str] = None


class UnitApprovalOut(UnitApproval):
    unit_info: Optional[UnitBase] = None
    gallery: list[GalleryItem] = []


class UnitOutPublic(UnitBase):
    #! which price should be shown here?
    starting_price: UnitPricing
    # nightly_price: UnitPricing
    thumbnail: GalleryItem = GalleryItem(
        order=0, url="https://jtrepair.com/wp-content/uploads/2019/02/placeholder-image11.jpg", type=GalleryType.image, alt_text="placeholder")


class UnitBookingOut(BaseModel):
    unit: UnitOutPublic
    booking: BookingOutPublic
    owner: ProfileOutPublic


class BookingInUnit(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    customer_id: str
    booking_date: datetime
    check_in_date: datetime
    check_out_date: datetime
    price: float
    currency: Currency


class UnitOutPublicDetailed(UnitBase):
    amenities: UnitAmenities
    is_approved: bool = False
    is_active: bool = False
    owner: ProfileOutPublic
    blocked_list: list[BlockedDate] = []
    pricing_list: list[UnitPricing] = []
    booked_list: list[BookingInUnit] = []
    gallery: list[GalleryItem] = []


class UnitOutAdmin(UnitBase):
    approval_logs: list[UnitApproval] = []
    amenities: UnitAmenities
    is_approved: bool = False
    is_active: bool = False
    is_draft: bool = False
    gallery: list[GalleryItem] = []
    completed_bookings: Optional[int] = None
    upcoming_bookings: Optional[int] = None
    started_bookings: Optional[int] = None
    owner_name: Optional[str] = None
    owner_subscription_end_date: Optional[datetime] = None
    pricing_list: list[UnitPricing] = []
    booked_list: list[BookingInUnit] = []
    blocked_list: list[BlockedDate] = []


class UnitOutApprovals(UnitOutPublicDetailed):
    approval: Optional[UnitApproval] = None


class UnitInDB(UnitBase):
    amenities: UnitAmenities
    approval_logs: list[UnitApproval] = []
    pricing_list: list[UnitPricing] = []
    booked_list: list[BookingInUnit] = []
    blocked_list: list[BlockedDate] = []
    gallery: list[GalleryItem] = []
    is_approved: bool = False
    is_draft: bool = False
    is_active: bool = False


class LocationInDB(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    name: str
    name_l1: str
    level: LocationLevel = LocationLevel.country
    parent_id: Optional[str] = None
    children: list[LocationItem] = []


class SearchFilters(BaseModel):
    keywords: Optional[str] = None
    unit_type: Optional[UnitType] = None
    country: Optional[str] = None
    city: Optional[str] = None
    area: Optional[str] = None
    package: Optional[UnitBookingType] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    price_from: Optional[float] = None
    price_to: Optional[float] = None

    num_floors: Optional[int] = None
    num_master_bedrooms: Optional[int] = None
    num_single_bedrooms: Optional[int] = None
    num_bathrooms: Optional[int] = None
    num_living_rooms: Optional[int] = None

    num_private_pool: Optional[int] = None
    num_shared_pool: Optional[int] = None

    nanny_room: Optional[bool] = None
    driver_room: Optional[bool] = None
    garden: Optional[bool] = None
    elevator: Optional[bool] = None
    suitable_for_elderly_disabled: Optional[bool] = None
    sea_nearby: Optional[bool] = None
    wifi: Optional[bool] = None
    kitchen_utensils: Optional[bool] = None

    #! add more filters here
