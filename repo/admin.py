from models.users import UserInDB
from models.owner import OwnerInDB
from models.owner import OwnerOut
from models.units import UnitOutApprovals
from models.units import UnitInDB
from typing import Optional
from models.units import UnitApproval, ApprovalStatus, ApprovalType
from datetime import datetime
from abc import ABC, abstractmethod

from models.customer import CustomerInDB
from pymongo import MongoClient
from models.common import PaginationIn, PaginatedList, PaginationOut
from repo.db import MongoDB
from bson import ObjectId
from models.units import UnitApproval
from util.misc import db_to_dict
from models.users import AdminInDB


def get_admin_from_auth_user(auth_user):
    admin = MongoDB.admin.find_one({"auth_user_id": auth_user.id})
    return AdminInDB(**db_to_dict(admin))


def get_approvals(page: PaginationIn, approval_status: Optional[ApprovalStatus] = None, approval_type: ApprovalType = ApprovalType.creation) -> PaginatedList[UnitOutApprovals]:

    if approval_status is None:
        raise Exception("approval_status cannot be None")
    
    if approval_type is ApprovalType.creation:
        units = MongoDB.units.find({"approval_logs.approval_status": approval_status,
                                    "approval_logs.approval_type": ApprovalType.creation}).skip((page.page-1)*page.limit).limit(page.limit)

    # NOTE: This assumes that approval_logs are only made once per unit for each approval_type, for now only creation
    units = list(UnitInDB(**db_to_dict(unit)) for unit in units)
    # create a list of unit_approvals with datatype UnitApproval
    unit_approvals_list = []
    # find owners for each unit
    owners_db = MongoDB.owner.find(
        {"_id": {"$in": [ObjectId(unit.owner_id) for unit in units]}})
    owners_db = list(OwnerInDB(**db_to_dict(owner)) for owner in owners_db)
    # owners_auth_users = MongoDB.authuser.find(
    #     {"_id": {"$in": [ObjectId(owner.auth_user_id) for owner in owners_db]}})
    # owners_auth_users = list(
    #     UserInDB(**db_to_dict(auth_user)) for auth_user in owners_auth_users)
    # match owners to auth users
    from models.owner import ProfileOutPublic
    owners = [ProfileOutPublic(**owner.contact.dict(), _id=owner.id)
              for owner in owners_db]

    out_approvals = []

    for idx, unit in enumerate(units):
        for owner in owners:
            if owner.id == unit.owner_id:
                out_approvals.append(UnitOutApprovals(_id=unit.id,
                                                      **unit.dict(), owner=owner))
                break

        if approval_type == ApprovalType.creation:
            if len(unit.approval_logs) < 1:
                # add a blank approval log
                unit.approval_logs.append(UnitApproval(
                    unit_id=unit.id, admin_id=None, time_created=datetime.utcnow(), time_updated=datetime.utcnow(),
                    approval_type=ApprovalType.creation, approval_status=ApprovalStatus.pending))
                # add the approval log to the unit
                # FIXME bad practice to update the db here
                MongoDB.units.update_one({"_id": ObjectId(unit.id)}, {
                    "$set": {"approval_logs": [approval.dict() for approval in unit.approval_logs]}})

        for approval_log in unit.approval_logs:
            if approval_log.approval_type == approval_type:
                # check because if approval_status is None then we want all approvals
                if approval_status is not None:
                    if approval_log.approval_status == approval_status:
                        out_approvals[idx].approval = approval_log
                else:
                    out_approvals[idx].approval = approval_log

    return PaginatedList(
        data=out_approvals,
        pagination=PaginationOut(
            total=MongoDB.units.count_documents({"approval_logs.approval_status": approval_status,
                                                 "approval_logs.approval_type": approval_type}), page=page.page,
            num_items=page.limit)
    )
