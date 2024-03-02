from models.owner import OwnerInDB
from repo.owner import get_owners_by_id
from models.units import ApprovalStatus, ApprovalType, UnitOutAdmin, UnitOutApprovals, UnitApproval
from models.subscriptions import SubscriptionType
from services.owner import renew_owner_subscription as renew_owner_subscription_service
from services.owner import register_owner, get_owner_current_subscription
from fastapi import APIRouter, Header, HTTPException, Form, UploadFile, File, Depends, Query, Path, Body
from models.common import PaginationIn, PaginationOut, PaginatedList, SortQuery
from models.units import *
from auth.models import UserOut, RoleEnum
from models.owner import OwnerCreate, OwnerOut
from models.subscriptions import OwnerSubscriptionOut, OwnerSubscriptionIn
from util.security import verify_token_header, access_check
from pydantic import EmailStr

admin = APIRouter(prefix="/admin", tags=["admin"])

# Unit Approval Management
# TODO: GET /units/approval - get all unapproved units + pagination
# TODO: POST /units/approve/{unit_id} - approve unit action (includes add, remove, edit)
# TODO: POST /units/reject/{unit_id} - reject unit action (includes add, remove, edit)
# TODO: GET /units/ - get all units + pagination + admin details/filters

# User Management
# TODO: GET /users/{user_type} - get all users + pagination + by user type (owner, customer, admin)
# TODO: POST /users/owner/create - create owner
# TODO: PATCH /users/owner/refresh-password - refresh owner password
# TODO: PATCH /users/owner/edit - edit owner data
# TODO: DELETE /users/owner/delete - delete owner

# User Subscription Management
# TODO: GET /users/owner/subscription - get owner subscription
# TODO: POST /users/owner/subscription - create owner subscription
# TODO: PUT /users/owner/subscription - renew owner subscription
# TODO: DELETE /users/owner/subscription - delete owner subscription

# Audit Logs

# Statistics
# [X] DB
# [ ] Tests


@admin.get("/units/approval", response_model=PaginatedList[UnitOutApprovals])
async def get_unapproved_units(is_approved: ApprovalStatus = Query(ApprovalStatus.pending, description="Filter by approval status", example=ApprovalStatus.pending),
                               pagination: PaginationIn = Depends(
                                   PaginationIn),
                               auth_user: UserOut = Depends(verify_token_header)):
    access_check(auth_user, "admin")
    '''Get all unapproved units (ordered by newest first)'''
    from repo.admin import get_approvals
    return get_approvals(page=pagination, approval_status=is_approved)


# [ ] DB
# [ ] Tests


@admin.post("/units/approve/{unit_id}")
async def approve_unit(
    review: Optional[str] = Body(
        None, description="Admin review of the unit", example="Unit is good"),
    unit_id: str = Path(
        ..., description="Unit ID", example="60d4a1b0a6b7a7c7a9a9a9a9"),
    new_status: ApprovalStatus = Body(
        ..., description="New approval status", example=ApprovalStatus.approved),
    auth_user: UserOut = Depends(verify_token_header)
):
    '''Approve unit action (includes approve, reject, suspend)'''
    access_check(auth_user, "admin")

    from repo.admin import get_admin_from_auth_user
    from models.units import ApprovalType
    from services.admin import set_approval_status
    admin_id = get_admin_from_auth_user(auth_user).id
    try:
        set_approval_status(
            unit_id=unit_id,
            approval_status=new_status,
            admin_id=admin_id,
            admin_review=review,
            approval_type=ApprovalType.creation
        )
        return {"message": "Unit approval status update to " + new_status + " successful"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# [ ] DB
# [ ] Tests


@admin.get("/units/", response_model=PaginatedList[UnitOutAdmin])
async def get_all_units(
        auth_user: UserOut = Depends(verify_token_header),
        pagination: PaginationIn = Depends(PaginationIn),
        subscribed_only: bool = Query(
            False, description="Filter by subscribed owners only"),
        active_only: bool = Query(
            False, description="Filter by active units only")
):
    '''Get all units (ordered by newest first)'''
    access_check(auth_user, "admin")
    from repo.units import get_all_units
    units_db = get_all_units(
        pagination=pagination, subscribed_only=subscribed_only, is_active=active_only).data
    if len(units_db) == 0:
        raise HTTPException(status_code=404, detail="No units found")
    # TODO .. this should be done in repo or service layer
    owners = get_owners_by_id([unit.owner_id for unit in units_db])
    units = []
    for unit in units_db:
        # count number of approved bookings from the booking array (upcoming and past)
        upcoming_count = 0
        started_count = 0
        completed_count = 0
        for booking in unit.booked_list:
            booking = BookingInUnit(**booking.dict())
            if booking.check_in_date > datetime.utcnow():
                upcoming_count += 1
            elif booking.check_in_date <= datetime.utcnow() and booking.check_out_date >= datetime.utcnow():
                started_count += 1
            elif booking.check_out_date < datetime.utcnow():
                completed_count += 1
        # get owner name
        owner_name = ""
        owner_subscription_end_date = None
        for owner in owners:
            if owner.id == unit.owner_id:
                owner_name = owner.contact.name
                owner_subscription_end_date = owner.subscription_end_date
                break

        units.append(UnitOutAdmin(**unit.dict(), _id=unit.id, completed_bookings=completed_count,
                     upcoming_bookings=upcoming_count, started_bookings=started_count,
                     owner_name=owner_name, owner_subscription_end_date=owner_subscription_end_date))
    return PaginatedList[UnitOutAdmin](data=units, pagination=PaginationOut(page=pagination.page, num_items=pagination.limit, total=len(units), total_pages=len(units)//pagination.limit))

# [ ] DB
# [ ] Tests


@admin.get("/users/{user_type}", response_model=PaginatedList[UserOut], description="Get all users (default ordered by name ) by user type (owner, customer, admin)")
async def get_all_users(
        user_type: RoleEnum = Path(
            ..., description="User type", example=RoleEnum.owner),
        sort_query: SortQuery = Depends(SortQuery),
        auth_user: UserOut = Depends(verify_token_header)
):
    '''Get all users (default ordered by name ) by user type (owner, customer, admin)'''
    access_check(auth_user, "admin")
    # if UserType chosen is none then return all users
    # 501 Not Implemented
    raise HTTPException(status_code=501, detail="Not Implemented")

# [X] Response Model
# [X] Request Model
# [X] Auth
# [ ] DB
# [ ] Tests


@admin.post("/users/owner/create", response_model=OwnerOut)
async def create_owner(owner: OwnerCreate = Body(..., description="Owner data"),
                       init_subscription: Optional[SubscriptionType] = Body(
                           None, description="Initial subscription data"),
                       auth_user: UserOut = Depends(verify_token_header)):
    '''Creates an owner account'''
    # check if admin is allowed to create owner
    access_check(auth_user, "admin")
    # call create owner service
    try:
        owner = register_owner(
            new_owner=owner, subscription_type=init_subscription)
        return owner
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# [X] Response Model
# [X] Request Model
# [X] Auth
# [ ] DB
# [ ] Tests
@admin.patch("/users/owner/change-password", description="Update owner password", response_model=UserOut)
async def change_owner_password(new_password: str = Body(..., description="New password"),
                                owner_id: str = Query(None,
                                                      description="Owner ID"),
                                username: str = Query(None,
                                                      description="Owner username"),
                                email: EmailStr = Query(None,
                                                        description="Owner email"),
                                phone_number: str = Query(None,
                                                          description="Owner phone number"),
                                auth_user: UserOut = Depends(verify_token_header)):
    """ An admin can change the password of an owner by providing the owner's ID, username or phone number"""
    access_check(auth_user, "admin")
    from repo.auth_user import update_password, get_auth_user_by_id
    from repo.owner import get_owner_by_id
    from repo.auth_user import get_auth_user_by_email, get_auth_user_by_username
    try:
        auth_user = None
        if email is not None:
            auth_user = get_auth_user_by_email(email)
        if username is not None:
            auth_user = get_auth_user_by_username(username)
        if auth_user is not None:
            # check if owner
            if auth_user.role != RoleEnum.owner:
                raise HTTPException(status_code=400,
                                    detail="User is not an owner")
        if owner_id is not None:
            auth_user = get_owner_by_id(owner_id).auth_user
    except:
        raise HTTPException(status_code=404, detail="Owner not found")
    try:
        update_password(auth_user, new_password)
        return get_auth_user_by_id(auth_user.id)
    except:
        raise HTTPException(status_code=400, detail="Password update failed")

# # [ ] Response Model
# # [ ] Request Model
# # [ ] Auth
# # [ ] DB
# # [ ] Tests
# @admin.patch("/users/owner/edit")
# async def edit_owner():
#     # 501 Not Implemented
#     raise HTTPException(status_code=501, detail="Not Implemented")

# [X] Response Model
# [X] Request Model
# [X] Auth
# [ ] DB
# [ ] Tests


@admin.delete("/users/owner/delete", response_model=OwnerOut)
async def delete_owner(hard_delete: bool = Query(False, description="Hard delete owner and all units"),
                       owner_id: str = Query(..., description="Owner ID"),
                       auth_user: UserOut = Depends(verify_token_header)):
    '''Deletes owner and all units (hard delete if hard_delete is true))'''
    access_check(auth_user, "admin")
    # Disables owner and all units (soft delete)
    # 501 Not Implemented
    raise HTTPException(status_code=501, detail="Not Implemented")


# [X] Response Model
# [X] Request Model
# [X] Auth
# [ ] DB
# [ ] Tests


@admin.put("/users/owner/subscription", response_model=OwnerSubscriptionOut)
async def renew_owner_subscription(
        owner_id: str = Query(None, description="Owner ID"),
        auth_user: UserOut = Depends(verify_token_header)):
    '''Renew owner subscription and update expiry date depending on current subscription type'''
    access_check(auth_user, ["admin", "owner"])
    if owner_id is None:
        owner_id = auth_user.owner_id
    if auth_user.role == RoleEnum.owner and auth_user.owner_id != owner_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    try:
        renew_owner_subscription_service(owner_id)
        return get_owner_current_subscription(owner_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# [X] Response Model
# [X] Request Model
# [X] Auth
# [ ] DB
# [ ] Tests


@admin.delete("/users/owner/subscription", response_model=OwnerSubscriptionOut)
async def cancel_owner_subscription(
        owner_id: str = Query(..., description="Owner ID"),
        auth_user: UserOut = Depends(verify_token_header)):
    '''Cancel owner subscription'''
    access_check(auth_user, "admin")
    # 501 Not Implemented
    raise HTTPException(status_code=501, detail="Not Implemented")


@admin.delete("/units/{unit_id}")
async def delete_unit(unit_id: str = Path(..., description="Unit ID"),
                      auth_user: UserOut = Depends(verify_token_header)):
    '''HARD DELETE a unit by its ID. (Deletes unit and all bookings for this unit)'''
    access_check(auth_user, "admin")
    from repo.units import hard_delete_unit
    try:

        if hard_delete_unit(unit_id):
            return {"message": "Unit deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Unit not found")
    except:
        raise HTTPException(status_code=400, detail="Unit deletion failed")

# get all unsubscribed owners


@admin.get("/users/owner/unsubscribed", response_model=list[OwnerInDB])
async def get_unsubscribed_owners(
        auth_user: UserOut = Depends(verify_token_header),
        pagination: PaginationIn = Depends(PaginationIn)
):
    '''Get all unsubscribed owners (ordered by newest first)'''
    access_check(auth_user, "admin")
    from repo.owner import get_all_unsubscribed_owners
    return get_all_unsubscribed_owners()
