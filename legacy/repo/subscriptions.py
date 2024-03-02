
from models.owner import OwnerInDB
from models.subscriptions import OwnerSubscriptionOut
from models.subscriptions import SubscriptionOut
from repo.db import MongoDB
from bson import ObjectId
from datetime import datetime
from util.misc import db_to_dict
from util.subscriptions import infer_subscription_status


def get_subscription_by_id(subscription_id: str) -> SubscriptionOut:
    """Gets a subscription by ID."""
    subscription = MongoDB.subscriptions.find_one(
        {"_id": ObjectId(subscription_id)})
    # check if subscription exists
    if subscription is None:
        raise Exception("Subscription not found")
    status = infer_subscription_status(
        subscription["start_date"], subscription["end_date"], subscription["subscription_type"])
    return SubscriptionOut(**db_to_dict(subscription), status=status)


def get_owner_subscription(owner_id: str) -> OwnerSubscriptionOut:
    """Gets an owner's subscription."""
    # this should be refactored but im too lazy
    owner = MongoDB.owner.find_one({"_id": ObjectId(owner_id)})
    if owner is None:
        raise Exception("Owner not found")
    owner = OwnerInDB(**db_to_dict(owner))

    owner_subscription = MongoDB.subscriptions.find_one(
        {"_id": ObjectId(owner.subscription_id)})
    status = infer_subscription_status(
        owner_subscription["start_date"], owner_subscription["end_date"], owner_subscription["subscription_type"])
    
    owner_subscription = OwnerSubscriptionOut(**db_to_dict(owner_subscription), status=status)

    return owner_subscription
