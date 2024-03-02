from datetime import datetime
from models.units import UnitApproval
from bson import ObjectId
from auth.models import AdminInDB
from models.units import UnitInDB
from typing import Optional
from models.units import UnitApproval, ApprovalStatus, ApprovalType
from models.subscriptions import SubscriptionType
from auth.models import RoleEnum, UserIn
from auth.repo import create_auth_user
from repo.db import MongoDB
from util.misc import db_to_dict
from pydantic import EmailStr

# SUPER ADMIN


def create_admin(username: str, password: str, email: EmailStr) -> str:
    """Creates an admin."""

    # create an auth user
    auth_user_in = UserIn(
        username=username,
        password=password,
        role=RoleEnum.admin,
        email=email,
    )
    auth_user = create_auth_user(
        auth_user_in
    )
    # create an admin
    from auth.models import AdminInDB
    admin = AdminInDB(
        auth_user_id=str(auth_user.id),
    )
    admin_id = MongoDB.admin.insert_one(admin.dict()).inserted_id
    # admin = MongoDB.admin.find_one({"_id": admin_id})
    # admin = AdminInDB(**db_to_dict(admin))
    return admin


def set_approval_status(unit_id: str, approval_status: str,  admin_review: str, admin_id: Optional[str] = None, approval_type: ApprovalType = ApprovalType.creation):
    # find unit by id
    from repo.units import get_unit_by_id
    unit = get_unit_by_id(unit_id)
    # or if not found and is_approved is false then create a new approval_log with creation type
    if len(unit.approval_logs) == 0:
        unit.approval_logs.append(UnitApproval(
            unit_id=unit_id,
            admin_id=admin_id,
            admin_review=admin_review,
            approval_status=approval_status,
            approval_type=approval_type,
            time_created=datetime.utcnow(),
            time_updated=datetime.utcnow()
        ))

    # look for approval_type in unit.approval_logs
    if len(unit.approval_logs) > 0:
        for approval in unit.approval_logs:
            # update approval with matching approval_types
            if approval.approval_type == approval_type:
                approval.approval_status = approval_status
                if approval_type == ApprovalType.creation:
                    if approval_status == ApprovalStatus.approved:
                        unit.is_approved = True
                        unit.is_active = True
                        unit.is_draft = False
                    else:
                        unit.is_approved = False
                        unit.is_active = False
                        unit.is_draft = True

                approval.admin_id = admin_id
                approval.admin_review = admin_review
                approval.unit_id = unit_id
                approval.time_updated = datetime.utcnow()
                break

    if approval_status == ApprovalStatus.approved and approval_type == ApprovalType.creation:
        # if approval_status is approved and approval_type is creation
        # update the unit status to active
        unit.is_active = True
        unit.is_draft = False
        unit.is_approved = True

    # update the element with that approval_type
    MongoDB.units.update_one({"_id": ObjectId(unit_id)}, {"$set": unit.dict()})
    from models.units import UnitOutAdmin
    return UnitOutAdmin(**unit.dict(), _id=unit.id)

# class SubscriptionManager():
#     def get_user_subscriptions(self, user_id: str) -> list:
#         """Gets all subscriptions for a user."""
#         return self.get_collection().find({"user_id": user_id})

#     def renew_subscription(self, subscription_id :str, renewal_interval: SubscriptionType) -> str:
#         """Renews a subscription."""
#         subscription = self.get_by_id(subscription_id)
#         subscription["renewal_interval"] = renewal_interval
#         # update the subscription in the database

#         return new_subscription_id

#     def cancel_subscription(self, subscription_id: str) -> str:
#         """Cancels a subscription."""
#         subscription = self.get_by_id(subscription_id)
#         subscription["status"] = "cancelled"
#         # update the subscription in the database

#         return new_subscription_id

# class OwnerService():
#     def get_owner_profile(self, owner_id: str) -> dict:
#         """Gets an owner's profile."""
#         pass

#     def update_owner_profile(self, owner_id: str, profile: dict) -> dict:
#         """Updates an owner's profile."""
#         pass

#     def get_owner_subscriptions(self, owner_id: str) -> list:
#         """Gets all subscriptions for an owner."""
#         pass

#     def get_owner_units(self, owner_id: str) -> list:
#         """Gets all units for an owner."""
#         pass
#     def register_owner(self, owner_id: str) -> str:
#         """Registers an owner."""
#         pass
#     def delete_owner(self, owner_id: str) -> str:
#         """Deletes an owner."""
#         pass
