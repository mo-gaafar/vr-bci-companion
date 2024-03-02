from models.owner import ProfileOutPublic
from models.booking import BookingInDB, BookingOutOwner, BookingOutOwnerDetailed
from repo.owner import get_owner_by_id
from repo.subscriptions import get_subscription_by_id
from models.subscriptions import SubscriptionOut
from models.subscriptions import OwnerSubscriptionOut
from typing import Optional
from models.subscriptions import SubscriptionType

from repo.db import MongoDB
from models.owner import OwnerCreate, OwnerOut
from auth.models import RoleEnum, UserOut
from models.subscriptions import SubscriptionInDB
from util.security import hash_password
from datetime import datetime, timedelta


from util.misc import id_to_str
from util.subscriptions import get_time_shifted
from bson import ObjectId
from util.misc import db_to_dict
from models.owner import OwnerInDB


def register_owner(new_owner: OwnerCreate, subscription_type: Optional[SubscriptionType]) -> str:
    """Registers an owner."""
    # create a new auth user
    from auth.models import UserIn

    from auth.repo import create_auth_user
    new_owner.auth_user.role = RoleEnum.owner
    auth_user = create_auth_user(new_owner.auth_user)

    # create a new owner
    from models.owner import OwnerInDB
    owner = OwnerInDB(
        auth_user_id=str(auth_user.id),
        contact=new_owner.contact,
    )
    owner_id = str(MongoDB.owner.insert_one(owner.dict()).inserted_id)

    # create a new subscription
    if subscription_type is not None:
        renew_owner_subscription(owner_id, subscription_type)

    # get the owner
    owner = MongoDB.owner.find_one({"_id": ObjectId(owner_id)})
    owner = OwnerInDB(**db_to_dict(owner))
    return OwnerOut(
        **owner.dict(),
        auth_user=UserOut(**auth_user.dict(), _id=auth_user.id),
    )



def get_owner_profile(owner_id: str) -> dict:
    """Gets an owner's profile."""
    pass


def update_owner_profile(owner_id: str, profile: dict) -> dict:
    """Updates an owner's profile."""
    pass


def check_owner_subscription(owner_id: str) -> bool:
    """Checks if an owner has a valid subscription."""
    try:
        subscription = get_owner_current_subscription(owner_id)
        if subscription.status == "active":
            return True
        return False
    except Exception as e:
        print(e)
        return False


def get_owner_current_subscription(owner_id) -> OwnerSubscriptionOut:
    """Gets an owner's current subscription."""
    owner = MongoDB.owner.find_one({"_id": ObjectId(owner_id)})
    owner = OwnerInDB(**db_to_dict(owner))
    subscription_out = OwnerSubscriptionOut(_id=owner.subscription_id,
                                            **(get_subscription_by_id(owner.subscription_id).dict()),
                                            owner=get_owner_by_id(owner_id))
    return subscription_out


def renew_owner_subscription(owner_id: str, subscription_type: Optional[SubscriptionType] = None, start_date: datetime = datetime.utcnow(), force_renew: bool = False) -> str:
    """Renews an owner's subscription."""

    # get the subscription type and end date from the owner's current subscription
    owner = MongoDB.owner.find_one({"_id": ObjectId(owner_id)})
    if owner is None:
        raise Exception("Cannot renew subscription, owner not found")
    subscription_id = owner.get("subscription_id")
    subscription = MongoDB.subscriptions.find_one(
        {"_id": ObjectId(subscription_id)})

    if subscription is not None:
        end_date = subscription.get("end_date")
        if subscription_type is None:
            subscription_type = subscription.get("subscription_type")
            if subscription_type is None:
                raise Exception(
                    "Cannot renew subscription, no subscription type given")

    # only renew if the subscription is going to expire in 7 days or if force is true
        if end_date > datetime.utcnow() + timedelta(days=7) and force_renew is False:
            raise Exception(
                "Cannot renew subscription, it is not expiring soon. Subscriptions must be renewed within 7 days of expiry.")
        # set the start date to the end date of the current subscription
        start_date = datetime(subscription.get("end_date"))

    from models.subscriptions import SubscriptionInDB
    if subscription_type is None:
        raise Exception("Cannot renew subscription, no subscription type given")
    # calculate the end date of the subscription based on the subscription type
    from util.subscriptions import get_time_shifted
    end_date = get_time_shifted(start_date, subscription_type)

    # create a new subscription in the database
    subscription = SubscriptionInDB(
        subscriber_id=owner_id,
        subscriber_type=RoleEnum.owner,
        subscription_type=subscription_type,
        end_date=end_date,
        start_date=start_date,
    )
    subscription_id = str(MongoDB.subscriptions.insert_one(
        subscription.dict()).inserted_id)

    # update the owner with the subscription id and subscription_end_date
    MongoDB.owner.update_one(
        {"_id": ObjectId(owner_id)},
        {"$set": {
            "subscription_id": subscription_id,
            "subscription_end_date": end_date,
        }}
    )

    return subscription_id


def delete_owner(owner_id: str) -> str:
    """Deletes an owner."""
    pass


def get_detailed_booking_for_owner(owner_id: str, booking_id: str) -> BookingOutOwnerDetailed:
    """Gets a detailed booking for an owner."""
    booking = MongoDB.booking.find_one(
        {"_id": ObjectId(booking_id), "owner_id": owner_id})
    if booking is None:
        raise Exception("Booking not found")
    booking = BookingInDB(**db_to_dict(booking))

    # get the customer
    from repo.customer import get_customer_by_id
    customer = get_customer_by_id(booking.customer_id)
    if customer is None:
        raise Exception("Customer not found")

    return BookingOutOwnerDetailed(
        **booking.dict(),
        customer=ProfileOutPublic(**customer.dict(), _id=customer.id,
                                  name=customer.first_name + " " + customer.last_name),
    )



