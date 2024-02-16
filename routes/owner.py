from models.notifications import OwnerNotification, OwnerNotificationType
from repo.owner import get_owner_by_auth_user_id
from services.owner import get_owner_current_subscription
from models.subscriptions import OwnerSubscriptionOut
from fastapi import APIRouter, Header, HTTPException, Form, UploadFile, File, Depends, Query, Path, Body
from models.units import *
from models.users import UserOut, RoleEnum
from models.common import PaginationIn, PaginationOut, PaginatedList, DateRange
from models.booking import *
from models.shared import *
from util.security import optional_token_header, verify_token_header, access_check
from typing import Optional


owner = APIRouter(prefix="/owner", tags=["owner"])


# Owner Profile Management
# ~TODO: POST /owner/register - ! self register (for future use)
# ~TODO: GET /owner/profile
# ~TODO: PUT /owner/profile/update

# Owner Unit Management
# TODO: GET /owner/units/all - get all units for owner + pagination
# TODO: GET /owner/units/active - get all active units for owner + pagination
# TODO: GET /owner/units/{unit_id}/bookings - get all bookings for unit + future or past (default all)
# TODO: PUT /owner/units/{unit_id}/bookings/{booking_id} - update booking status
# TODO: GET /owner/units/{unit_id}/bookings/{booking_id} - get booking details
# TODO: PUT /owner/units/{unit_id}/blocked_dates - update blocked dates (add, remove, edit)


# Unit Creation Workflow
# 1. Create Unit Draft
# 2. Upload Images
# 2.1. Note first image is cover image
# 2.2. Note max 12 images/ video links
# 3. Submit for Approval
# TODO: POST /owner/units/create - create unit draft
# TODO: POST /owner/units/{unit_id}/upload - upload unit image (file upload)
# TODO: PUT /owner/units/{unit_id}/gallery/ - update unit media (add video link, image link, reorder , remove, edit)
# TODO: POST /owner/units/{unit_id}/submit - submit unit for approval

# TODO: PUT /owner/units/{unit_id}/ - update unit details (edit)
# TODO: DELETE /owner/units/{unit_id}/ - delete unit (soft delete)


# [ ] Response Model
# [ ] Request Model
# [ ] Auth
# [ ] DB
# [ ] Tests
# @owner.post("/register")
# async def register_owner():
#       # 501 Not Implemented
#       raise HTTPException(status_code=501, detail="Not Implemented")

# [X] Response Model
# [X] Request Model
# [ ] Auth
# [ ] DB
# [ ] Tests
@owner.get("/units/all", response_model=PaginatedList[UnitOutAdmin])
async def get_all_units_for_owner(owner_id=Query(None, description="Owner ID", example="60d4a1b0a6b7a7c7a9a9a9a9"),
                                  auth_user: UserOut = Depends(
                                      optional_token_header),
                                  pagination: PaginationIn = Depends(
                                      PaginationIn),
                                  ):
    '''Get all units (for an owner) - active or inactive (default all) or if no query param get from authentication token'''
    from repo.units import get_all_owner_units
    if auth_user is not None:
        access_check(auth_user, [RoleEnum.owner, RoleEnum.admin])
        if auth_user.role == "owner":
            if owner_id is None:
                # get owner id from auth user
                owner_id = get_owner_by_auth_user_id(auth_user.id).id
    elif owner_id is None:
        raise HTTPException(
            status_code=400, detail="Owner ID was not provided")
    try:
        return get_all_owner_units(owner_id, pagination)
    except:
        raise HTTPException(status_code=404, detail="Owner units not found")


# [X] Response Model
# [X] Request Model
# [X] Auth
# [ ] DB
# [ ] Tests
@owner.get("/units/{unit_id}/bookings", response_model=PaginatedList[UnitBookingOutOwner])
async def get_unit_bookings(unit_id: str = Path(..., description="Unit ID"),
                            auth_user: UserOut = Depends(verify_token_header),
                            pagination: PaginationIn = Depends(PaginationIn),
                            status_filter: Optional[BookingStatus] = Query(
                                None, description="Filter by booking status"),
                            date_filter: Optional[DateRange] = Depends(
                                DateRange),
                            ):
    '''Get all bookings (summarized) for a unit (for owner) - future or past (default all) '''
    access_check(auth_user, [RoleEnum.owner, RoleEnum.admin])

    unit = get_unit_by_id(unit_id)
    if unit is None:
        raise HTTPException(status_code=404, detail="Unit not found")
    if auth_user.role == "owner":
        # get owner id from auth user
        owner_id = get_owner_by_auth_user_id(auth_user.id).id
        from repo.units import get_unit_by_id
        if unit.owner_id != owner_id:
            raise HTTPException(
                status_code=403, detail="Unit does not belong to owner")
        # check if unit belongs to owner
    try:
        from repo.booking import get_unit_bookings
        return get_unit_bookings(unit_id, pagination, status_filter, date_filter)
    except:
        raise HTTPException(status_code=404, detail="Unit bookings not found")

# [X] Response Model
# [X] Request Model
# [ ] Auth
# [ ] DB
# [ ] Tests


@owner.patch("/bookings/{booking_id}", response_model=UnitBookingOutOwner)
async def update_booking_status(
        booking_id: str = Path(..., description="Booking ID"),
        booking_status: UpdateBookingStatus = Body(
            ..., description="Booking Status"),
        auth_user: UserOut = Depends(verify_token_header)):
    '''Update booking status by booking ID (for owner)'''
    access_check(auth_user, [RoleEnum.owner, RoleEnum.admin])

    from repo.owner import get_owner_by_auth_user_id
    if auth_user.role == "owner":
        # get owner id from auth user
        owner_id = get_owner_by_auth_user_id(auth_user.id).id

    try:
        from repo.booking import get_booking_by_id
        from repo.customer import get_customer_by_id
        from repo.booking import update_booking_status
        booking_db = update_booking_status(
            owner_id, booking_id, booking_status.status)
        return UnitBookingOutOwner(**booking_db.dict(),
                                   customer=get_customer_by_id(booking_db.customer_id))

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# [X] Response Model
# [X] Request Model
# [ ] Auth
# [ ] DB
# [ ] Tests


@owner.get("/bookings/{booking_id}/details", response_model=BookingOutOwnerDetailed)
async def get_booking_details_for_owner(
        booking_id: str = Path(..., description="Booking ID"),
        auth_user: UserOut = Depends(verify_token_header)):
    '''Get booking details by unit and booking ID (for owner)'''
    access_check(auth_user, [RoleEnum.owner, RoleEnum.admin])
    from repo.owner import get_owner_by_auth_user_id
    if auth_user.role == "owner":
        # get owner id from auth user
        owner_id = get_owner_by_auth_user_id(auth_user.id).id
    try:
        from services.owner import get_detailed_booking_for_owner
        return get_detailed_booking_for_owner(owner_id, booking_id)
    except:
        raise HTTPException(status_code=404, detail="Unit bookings not found")


# [X] Response Model
# [X] Request Model
# [ ] Auth
# [ ] DB
# [ ] Tests


@owner.put("/units/{unit_id}/blocked_dates", response_model=List[BlockedDate])
async def update_blocked_dates(
        unit_id: str = Path(..., description="Unit ID"),
        blocked_dates: List[BlockedDate] = Body(...,
                                                description="Blocked Dates"),
        auth_user: UserOut = Depends(verify_token_header)):
    '''Update (overwrite) blocked dates by unit ID (for owner)'''
    access_check(auth_user, [RoleEnum.owner, RoleEnum.admin])
    if auth_user.role == "owner":
        # get owner id from auth user
        owner_id = get_owner_by_auth_user_id(auth_user.id).id
        from repo.units import get_unit_by_id
        unit = get_unit_by_id(unit_id)
        if unit.owner_id != owner_id:
            raise HTTPException(
                status_code=403, detail="Unit does not belong to owner")
    try:
        from repo.units import update_blocked_dates
        result = update_blocked_dates(unit_id, blocked_dates)
        if result == True:
            return blocked_dates
        else:
            raise HTTPException(status_code=404, detail="Unit not found")
    except:
        raise HTTPException(status_code=404, detail="Unit not found")
    # 501 Not Implemented
    # raise HTTPException(status_code=501, detail="Not Implemented")

# [X] Response Model
# [X] Request Model
# [ ] Auth
# [ ] DB
# [ ] Tests


@owner.post("/units/create", response_model=UnitOutAdmin)
async def create_unit_draft(
        unit: UnitCreate = Body(..., description="Unit Details"),
        auth_user: UserOut = Depends(verify_token_header)):
    '''Create unit draft (this is the first step in unit creation) (for owner)'''
    access_check(auth_user, [RoleEnum.owner])
    # get owner id from auth user
    owner_id = get_owner_by_auth_user_id(auth_user.id).id
    from services.subscription import check_subscription_limits_owner_unit_creation
    check_subscription_limits_owner_unit_creation(owner_id)
    # create unit
    try:
        from services.units import create_draft_unit
        unit_db = UnitInDB(**unit.dict())
        unit_db.owner_id = owner_id
        unit = create_draft_unit(unit_db)
        return unit
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# [X] Response Model
# [X] Request Model
# [X] Auth
# [ ] DB
# [ ] Tests


@owner.post("/units/{unit_id}/upload", response_model=GalleryItem)
async def upload_unit_image(
        unit_id: str = Path(..., description="Unit ID"),
        file: UploadFile = File(..., description="Unit Image"),
        auth_user: UserOut = Depends(verify_token_header)):
    '''Upload unit image (file upload) (for owner)'''
    access_check(auth_user, [RoleEnum.owner, RoleEnum.admin])
    # if owner check if unit belongs to owner
    try:
        from util.images import upload_image
        from models.common import ImageFolder
        image_url = upload_image(file, ImageFolder.unit_images)
        # add image to unit
        from repo.units import add_gallery_item_to_unit
        item = GalleryItem(url=image_url, type=GalleryType.image, order=1)
        add_gallery_item_to_unit(unit_id, item)
        return item
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    except:
        raise HTTPException(status_code=500, detail="Internal Server Error")

# [X] Response Model
# [X] Request Model
# [X] Auth
# [ ] DB
# [ ] Tests


@owner.put("/units/{unit_id}/gallery", response_model=List[GalleryItem])
async def update_unit_media(
        unit_id: str = Path(..., description="Unit ID"),
        gallery_items: List[GalleryItem] = Body(...,
                                                description="Gallery Items"),
        auth_user: UserOut = Depends(verify_token_header)):
    '''Update (overwrite) unit media gallery (add video link, image link, reorder , remove, edit) (for owner)'''
    access_check(auth_user, [RoleEnum.owner, RoleEnum.admin])
    # 501 Not Implemented
    raise HTTPException(status_code=501, detail="Not Implemented")
# [X] Response Model
# [X] Request Model
# [X] Auth
# [ ] DB
# [ ] Tests


@owner.post("/units/{unit_id}/submit", response_model=UnitOutAdmin)
async def submit_unit_for_posting(
        unit_id: str = Path(..., description="Unit Draft ID to be submitted"),
        auth_user: UserOut = Depends(verify_token_header)):
    '''Submit unit for public posting (for owner)'''
    access_check(auth_user, [RoleEnum.owner, RoleEnum.admin])
    owner_id = None
    if auth_user.role == "owner":
        # get owner id from auth user
        owner_id = str(get_owner_by_auth_user_id(auth_user.id).id)
    from services.subscription import check_subscription_limits_owner_unit_creation
    check_subscription_limits_owner_unit_creation(owner_id)
    # check if unit belongs to owner
    try:
        from repo.units import get_unit_by_id
        unit = get_unit_by_id(unit_id)
        if owner_id is not None and unit.owner_id is not None and unit.owner_id != owner_id:
            raise HTTPException(
                status_code=400, detail="Unit does not belong to owner")

        # submit unit for approval
        from services.units import submit_unit_for_approval
        unit = submit_unit_for_approval(unit_id)

        return unit

    except:
        raise HTTPException(status_code=404, detail="Unit not found")


# [X] Response Model
# [X] Request Model
# [ ] Auth
# [ ] DB
# [ ] Tests


@owner.put("/units/{unit_id}", response_model=UnitBase)
async def update_unit_details(
        unit_id: str = Path(..., description="Unit ID"),
        unit: UnitBase = Body(..., description="Unit Details"),
        auth_user: UserOut = Depends(verify_token_header)):
    '''Update unit details (edit) (for owner)'''
    access_check(auth_user, [RoleEnum.owner, RoleEnum.admin])
    # 501 Not Implemented
    raise HTTPException(status_code=501, detail="Not Implemented")

# [X] Response Model
# [X] Request Model
# [ ] Auth
# [ ] DB
# [ ] Tests


@owner.delete("/units/{unit_id}")
async def delete_unit(unit_id: str = Path(..., description="Unit ID"),
                      auth_user: UserOut = Depends(verify_token_header)):
    '''Delete unit (soft delete) (for owner)'''
    from repo.units import soft_delete_unit
    access_check(auth_user, [RoleEnum.owner, RoleEnum.admin])
    if auth_user.role == "owner":
        # get owner id from auth user
        owner_id = get_owner_by_auth_user_id(auth_user.id).id
        from repo.units import get_unit_by_id
        unit = get_unit_by_id(unit_id)
        if unit.owner_id != owner_id:
            raise HTTPException(
                status_code=403, detail="Unit does not belong to owner")
    try:
        if soft_delete_unit(unit_id):
            return {"message": "Unit deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Unit not found")
    except:
        raise HTTPException(status_code=404, detail="Unit not found")


# [X] Response Model
# [X] Request Model
# [X] Auth
# [ ] DB
# [ ] Tests


@owner.get("/subscription", response_model=OwnerSubscriptionOut)
async def get_owner_subscription(owner_id: str = Query(None, description="Owner ID"),
                                 auth_user: UserOut = Depends(verify_token_header)):
    '''Get owner subscription'''

    access_check(auth_user, ["admin", "owner"])
    if auth_user.role == "owner":
        if owner_id is None:
            # get owner id from auth user
            owner_id = get_owner_by_auth_user_id(auth_user.id).id
    try:
        subscription = get_owner_current_subscription(owner_id)
        return subscription
    except:
        raise HTTPException(
            status_code=404, detail="Owner subscription not found")


@owner.get("/notifications", response_model=PaginatedList[OwnerNotification])
async def get_notifications(
    auth_user: UserOut = Depends(verify_token_header),
    pagination: PaginationIn = Depends(PaginationIn),
):
    # AUTH AND ACCESS CHECK
    access_check(auth_user, ["owner"])
    try:
        if auth_user.role == "owner":
            # get owner id from auth user
            owner_id = get_owner_by_auth_user_id(auth_user.id).id
    except:
        raise HTTPException(
            status_code=404, detail="Owner not found")

    try:
        from services.notification import get_owner_notification_queue
        return get_owner_notification_queue(pagination, owner_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
