from models.business import Business, Venue
from fastapi import HTTPException
from bson.objectid import ObjectId

from repository.db import admin_db


def get_business(tenant_id: str):
    business = admin_db.business.find_one({"tenant_id": tenant_id})
    if business is None:
        raise HTTPException(status_code=404, detail="Business not found")
    business["_id"] = str(business["_id"])
    return Business(**business)


def get_venue(db, venue_id: str):
    venue = db.venues.find_one({"_id": ObjectId(venue_id)})
    if venue is None:
        raise HTTPException(status_code=404, detail="Venue not found")
    venue["_id"] = str(venue["_id"])
    return Venue(**venue)
