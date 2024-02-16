

from models.units import UnitType
from models.units import LocationLevel, LocationItem, LocationInDB
from models.units import LocationLevel
from enum import Enum
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Header, Query, Path


utility = APIRouter(prefix="/utility", tags=["utility"])


class SchemaQuery(str, Enum):
    unit_types = "unit_types"
    booking_types = "booking_types"
    amenities = "amenities"
    subscription_types = "subscription_types"
    subscription_status = "subscription_status"


@utility.get("/schema")
async def get_enums(
        query: SchemaQuery = Query(..., description="Query for schema", example="locations")):
    '''Get schema for queried models'''
    if query == "unit_types":
        # return list of available unit types
        from models.units import UnitType
        return list(UnitType)
    if query == "booking_types":
        # return list of available booking types
        from models.booking import UnitBookingType
        return list(UnitBookingType)
    if query == "amenities":
        # return list of available amenities
        from models.units import UnitAmenities
        return list(UnitAmenities)
    if query == "subscription_types":
        # return list of available subscription types
        from models.subscriptions import SubscriptionType
        return list(SubscriptionType)
    if query == "subscription_status":
        # return list of available subscription status
        from models.subscriptions import SubscriptionStatus
        return list(SubscriptionStatus)

    raise HTTPException(status_code=400, detail="Invalid query")


@utility.get("/locations/", response_model=list[LocationItem])
async def get_locations(country: str = Query(None, description="Country", example="Kuwait"),
                        level_filter: LocationLevel = Query(
                            LocationLevel.city, description="Level of detail", example=1),
                        unit_type: UnitType = Query(None, description="Unit Type", example="chalet")):
    '''Get locations (Not fully implemented)'''

    placeholder_kw_cities = [
        LocationItem(name="Kuwait City", name_l1="مدينة الكويت",
                     level=LocationLevel.city, _id="1", latitude=29.3759, longitude=47.9774),
        LocationItem(name="Hawally", name_l1="حولي", level=LocationLevel.city,
                     _id="2", latitude=29.3402, longitude=48.0317),
        LocationItem(name="Salmiya", name_l1="السالمية", level=LocationLevel.city,
                     _id="3", latitude=29.327, longitude=48.080),
        LocationItem(name="Mishref", name_l1="مشرف", level=LocationLevel.city,
                     _id="4", latitude=29.2947, longitude=47.9503),
        LocationItem(name="Jabriya", name_l1="الجابرية", level=LocationLevel.city,
                     _id="5", latitude=29.3328, longitude=48.0667),
        LocationItem(name="Mubarak Al-Kabeer", name_l1="مبارك الكبير",
                     level=LocationLevel.city, _id="6", latitude=29.2722, longitude=48.1167),
        LocationItem(name="Farwaniya", name_l1="الفروانية",
                     level=LocationLevel.city, _id="7", latitude=29.2779, longitude=47.9561),
        LocationItem(name="Jahra", name_l1="الجهراء", level=LocationLevel.city,
                     _id="8", latitude=29.3361, longitude=47.6869),
        LocationItem(name="Fahaheel", name_l1="الفحيحيل", level=LocationLevel.city,
                     _id="10", latitude=29.082, longitude=48.133),
        LocationItem(name="Sabah Al Salem", name_l1="صباح السالم",
                     level=LocationLevel.city, _id="11", latitude=29.239, longitude=48.036),
        LocationItem(name="Al-Ahmadi", name_l1="الأحمدي", level=LocationLevel.city,
                     _id="12", latitude=29.0789, longitude=48.0825),
        LocationItem(name="Al-Khiran", name_l1="الخيران", level=LocationLevel.city,
                     _id="13", latitude=28.9029, longitude=48.1326),
        LocationItem(name="Al-Subiyah", name_l1="الصبية", level=LocationLevel.city,
                     _id="14", latitude=29.8611, longitude=48.0933),
        LocationItem(name="Sabah Al Ahmad Sea City", name_l1="مدينة صباح الأحمد البحرية",
                     level=LocationLevel.city, _id="15", latitude=29.288, longitude=48.031),
        LocationItem(name="Bnaider", name_l1="بنيدر", level=LocationLevel.city,
                     _id="16", latitude=28.9181, longitude=48.1117),
        LocationItem(name="Abdullah Port", name_l1="ميناء عبدالله",
                     level=LocationLevel.city, _id="17", latitude=29.8611, longitude=48.0933),
        LocationItem(name="Al Abdali", name_l1="العبدلي", level=LocationLevel.city,
                     _id="18", latitude=28.9181, longitude=48.1117),
        LocationItem(name="Al Wafra", name_l1="الوفرة", level=LocationLevel.city,
                     _id="19", latitude=28.9181, longitude=48.1117),
        LocationItem(name="Kabed", name_l1="الكبد", level=LocationLevel.city,
                     _id="20", latitude=28.9181, longitude=48.1117),
    ]
    if unit_type is not None:
        # filter by unit type
        ids_dict = {
            UnitType.chalet: ["13", "16", "14", "15"],
            UnitType.farm: ["18", "19", "14"],
            UnitType.rest_house: ["19", "20"]
        }
        placeholder_kw_cities = [
            city for city in placeholder_kw_cities if city.id in ids_dict[unit_type]]
    return placeholder_kw_cities
