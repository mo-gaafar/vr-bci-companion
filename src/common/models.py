from pydantic import BaseModel, Field, ValidationError, Json
from bson.objectid import ObjectId
from pydantic import BaseModel, Field, validator
from bson import ObjectId
# from bson.errors import InvalidId
from datetime import datetime
from typing import Optional, TypeVar, Generic, List, Any, Annotated
from enum import Enum
import uuid
from typing import Annotated
from pydantic_core import core_schema
from pydantic.json_schema import JsonSchemaValue


def short_uuid():
    generated_uuid = str(uuid.uuid4())
    shortened_uuid = generated_uuid.replace("-", "")[:8]
    return shortened_uuid


# # Represents an ObjectId field in the database.
# # It will be represented as a `str` on the model so that it can be serialized to JSON.


# class PyObjectId(str):
#     @classmethod
#     def __get_validators__(cls):
#         yield cls.validate

#     @classmethod
#     def validate(cls, value):
#         if not ObjectId.is_valid(value):
#             raise ValidationError("Invalid ObjectId")
#         return str(value)  # Ensure it's returned as a string


class ObjectIdPydanticAnnotation:
    @classmethod
    def validate_object_id(cls, v: Any, handler) -> ObjectId:
        if isinstance(v, ObjectId):
            return v

        s = handler(v)
        if ObjectId.is_valid(s):
            return ObjectId(s)
        else:
            raise ValueError("Invalid ObjectId")

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, _handler) -> core_schema.CoreSchema:
        assert source_type is ObjectId
        return core_schema.no_info_wrap_validator_function(
            cls.validate_object_id,
            core_schema.str_schema(),
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def __get_pydantic_json_schema__(cls, _core_schema, handler) -> JsonSchemaValue:
        return handler(core_schema.str_schema())
# class ObjId(ObjectId):
#     @classmethod
#     def __get_validators__(cls):
#         yield cls.validate

#     @classmethod
#     def validate(cls, v: str):
#         try:
#             return cls(v)
#         except InvalidId:
#             raise ValueError("Not a valid ObjectId")


class RepeatType(str, Enum):
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"


class ImageFolder(str, Enum):
    profile_pics = "profile_pics"
    unit_images = "unit_images"


class Currency(str, Enum):
    egp = "egp"
    usd = "usd"
    eur = "eur"
    gbp = "gbp"
    sar = "sar"
    aed = "aed"
    kwd = "kwd"

# class CommonModel(BaseModel):
#     id: Optional[ObjId] = Field(None, alias="_id")

#     class Config:
#         # populate_by_name = True
#         json_encoders = {ObjectId: str}


class CommonModel(BaseModel):

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat() + "Z"
        }

    # @validator('phone', check_fields=False)
    # def validate_egyptian_phone_number(cls, phone):
    #     # Validate the phone number format
    #     if not phone.startswith('01') or len(phone) != 11:
    #         raise ValueError('Invalid Egyptian phone number format')
    #     # + 0 1 2 3 4 5 6 7 8 9 10
    #     # + 2 0 1 1 5 2 7 7 0 0 8
    #     # Validate the carrier code
    #     carrier_code = phone[2:4]
    #     valid_carrier_codes = ['10', '11', '12', '14']
    #     if carrier_code not in valid_carrier_codes:
    #         raise ValueError('Invalid carrier for Egyptian phone number')

    #     return phone


class SuccessfulResponse(BaseModel):
    message: str = "Success"


class MongoBaseModel(CommonModel):
    id: Optional[Annotated[ObjectId, ObjectIdPydanticAnnotation]
                 ] = Field(None, alias="_id")

    # @validator('id')
    # def validate_object_id(cls, v):
    #     if not ObjectId.is_valid(v):
    #         raise ValueError('Invalid ObjectId')
    #     return str(v)  # Ensure string output

    # class Config:
    #     json_encoders = {ObjectId: str}
    #     arbitrary_types_allowed = True


class DateRange(CommonModel):
    start: Optional[datetime]
    end: Optional[datetime]


class PaginationIn(BaseModel):
    page: Optional[int] = 1  # which page to return
    limit: Optional[int] = 10  # how many items per page


class PaginationOut(BaseModel):
    page: int
    num_items: int
    total: int
    total_pages: int = 0

    @validator('total_pages', pre=True, always=True)
    def calculate_total_pages(cls, v, values):
        if values['num_items'] == 0:
            return 0  # Avoid division by zero

        return (values['total'] // values['num_items']) + 1


#! Note: T is a generic type. It can be replaced with any type , this is called type variable.
T = TypeVar('T')


class PaginatedList(BaseModel, Generic[T]):
    pagination: PaginationOut
    data: List[T] = []


class BaseResponse(BaseModel, Generic[T]):
    data: T
    detail: str = "Success"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class SortBy(str, Enum):
    name = "name"
    popularity = "popularity"
    relevance = "relevance"
    price = "price"
    rating = "rating"
    time_created = "time_created"
    time_updated = "time_updated"


class SortQuery(BaseModel):
    sort_by: SortBy = SortBy.time_created
    sort_order: Optional[SortOrder] = SortOrder.desc


class Histogram(BaseModel):
    count: int
    bin: float


class AnalyticSummary(CommonModel):
    total: int
    count: int
    average: float


class CustomerRetention(CommonModel):
    tier_name: str
    # venue_name: str
    total_mins_stayed: float
    avg_mins_stayed: float
    total_customers: int


class SalesHistogram(BaseModel):
    bin: float
    count: int
    total_amount: int


class PaymentMethodSummary(CommonModel):
    method_name: str
    total: int
    percentage_from_order_count: float
    percentage_from_total: float


class EmailBodyFields(BaseModel):
    venue_name: str
    support_contact: str


class EmailTemplate(CommonModel):
    subject: str
    greeting: str

    name: str
    image_url_top: str
    image_bottom: str
    body: str
    attachment: str

    footer: str
    signature: str
