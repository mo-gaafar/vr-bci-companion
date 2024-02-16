from fastapi import Depends
from datetime import datetime, timedelta
from cachetools import TTLCache
from models.units import UnitOutPublic
from models.common import PaginationIn, PaginationOut, PaginatedList
from models.subscriptions import OwnerSubscriptionOut, SubscriptionInDB, SubscriptionType, SubscriptionStatus
from datetime import datetime
from bson.objectid import ObjectId
from typing import Optional
from models.owner import OwnerCreate, OwnerOut, OwnerInDB, ProfileOutPublic
from models.users import RoleEnum, UserOut
from repo.db import MongoDB
from util.misc import db_to_dict, id_to_str
from util.subscriptions import infer_subscription_status


def get_owner_by_auth_user_id(auth_user_id) -> OwnerOut:
    """Gets an owner by their auth user ID."""
    owner = MongoDB.owner.find_one({"auth_user_id": auth_user_id})
    owner = OwnerInDB(**db_to_dict(owner))
    auth_user = MongoDB.authuser.find_one(
        {"_id": ObjectId(owner.auth_user_id)})
    owner_out = OwnerOut(_id=owner.id, contact=owner.contact,
                         auth_user=UserOut(**db_to_dict(auth_user)), subscription_end_date=owner.subscription_end_date)
    return owner_out


def get_owner_by_id(owner_id) -> OwnerOut:
    """Gets an owner by their ID."""
    owner = MongoDB.owner.find_one({"_id": ObjectId(owner_id)})
    owner = OwnerInDB(**db_to_dict(owner))
    auth_user = MongoDB.authuser.find_one(
        {"_id": ObjectId(owner.auth_user_id)})
    owner_out = OwnerOut(contact=owner.contact,
                         auth_user=UserOut(**db_to_dict(auth_user)), _id=owner.id, subscription_end_date=owner.subscription_end_date)
    return owner_out


def get_owner_by_id_db(owner_id) -> OwnerInDB:
    """Gets an owner by their ID."""
    owner = MongoDB.owner.find_one({"_id": ObjectId(owner_id)})
    owner = OwnerInDB(**db_to_dict(owner))
    return owner


def add_unit_to_owner(owner_id: str, unit_id: str) -> None:
    """Adds a unit to an owner's owned_unit_ids."""
    MongoDB.owner.update_one({"_id": ObjectId(owner_id)}, {
        "$push": {"owned_unit_ids": unit_id}
    })


def get_owner_subscriptions(owner_id: str) -> list:
    """Gets all subscriptions for an owner."""
    pass


# Define a cache with a TTL (time-to-live) of 1 minute
cache = TTLCache(maxsize=1, ttl=60)


def get_all_unsubscribed_owners() -> list[OwnerInDB]:
    """Gets all owners with no subscription or expired subscription."""
    # Try to get the result from the cache
    cached_result = cache.get("unsubscribed_owners")
    if cached_result is not None:
        print("Using cached result of unsubscribed owners")
        return cached_result
    print("Querying MongoDB for unsubscribed owners")
    owners = []

    # Query MongoDB for owners with expired subscriptions
    expired_subscription_owners = MongoDB.owner.find(
        {"subscription_end_date": {"$lte": datetime.utcnow()}})

    for owner in expired_subscription_owners:
        owners.append(OwnerInDB(**db_to_dict(owner)))

    # Query MongoDB for owners with no subscription
    no_subscription_owners = MongoDB.owner.find(
        {"subscription_end_date": None})
    for owner in no_subscription_owners:
        owners.append(OwnerInDB(**db_to_dict(owner)))

    # Cache the result for future use
    cache["unsubscribed_owners"] = owners

    return owners


def get_owners_by_id(id_arr: list[str]) -> list[OwnerInDB]:
    """Gets a list of owners by id."""

    owners = MongoDB.owner.find(
        {"_id": {"$in": [ObjectId(id) for id in id_arr]}})
    owners = [OwnerInDB(**db_to_dict(owner)) for owner in owners]
    return owners

