from repo.subscriptions import get_owner_subscription
from models.subscriptions import SubscriptionInDB
from models.owner import OwnerOut
from datetime import datetime
from repo.owner import get_owner_by_id, get_owner_by_auth_user_id, get_owner_by_id_db
from auth.models import UserOut

from fastapi import HTTPException


def check_subscription_of_authuser(auth_user: UserOut, raise_exception: bool = True):
    # if the user type is owner then
    if auth_user.role == "owner":
        # get owner by auth user id
        owner = get_owner_by_auth_user_id(auth_user.id)
        return check_subscription_by_owner_id(owner.id, raise_exception)


def check_subscription_by_owner_id(owner_id: str, raise_exception: bool = True):
    # check if owner has active subscription
    owner = get_owner_by_id_db(owner_id)
    if owner.subscription_end_date is None:
        # if not raise exception or return false
        if raise_exception:
            raise HTTPException(
                status_code=401, detail="User has no active subscription, please contact support")
        else:
            return owner
    elif owner.subscription_end_date < datetime.utcnow():
        if raise_exception:
            raise HTTPException(
                status_code=401, detail="User's subscription has expired as of " + owner.subscription_end_date.strftime("%d/%m/%Y %H:%M:%S")
                + ", please contact support to renew")
        else:
            return owner
    # if not raise exception or return false
    # if yes then return true
    pass


def check_subscription_limits_owner_unit_creation(owner_id):
    """checks if owner is allowed to create more units according to their subscription"""
    # check if owner has active subscription
    owner = check_subscription_by_owner_id(owner_id)
    # get owner units
    from repo.units import get_all_owner_units
    owner_units = get_all_owner_units(owner_id).data
    owner_subscription = get_owner_subscription(owner_id)
    # check if owner has exceeded max approved units
    approved_units_count = 0
    for unit in owner_units:
        if unit.is_approved:
            approved_units_count += 1

    if owner_subscription.max_units is not None and owner_subscription.max_units <= approved_units_count:
        raise HTTPException(
            status_code=400, detail="User has exceeded their max approved units, please contact support")
