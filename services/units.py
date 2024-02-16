from models.units import UnitInDB, UnitOutAdmin
from models.common import PaginationIn, PaginationOut, PaginatedList
from models.users import UserOut, RoleEnum
from models.units import UnitInDB, UnitOutPublic, UnitType, UnitLocation,  UnitAmenities,  UnitPricing, UnitBookingType, GalleryItem
from repo.db import MongoDB
from bson import ObjectId


def upload_unit_image(unit_id: str, image: bytes, order: int, alt: str = None) -> GalleryItem:
    """Uploads an image to a unit."""
    # upload image to cloud storage
    from util.images import upload_image
    link = upload_image(image, "units")
    # id is the last part of the link
    id = link.split("/")[-2]
    gallery_item = GalleryItem(link=link, order=order, id=id, alt_text=alt)
    from repo.units import add_gallery_item_to_unit
    add_gallery_item_to_unit(unit_id, gallery_item)

    return gallery_item


def create_draft_unit(unit: UnitInDB) -> UnitOutAdmin:
    """Creates a draft unit."""
    # lock unit creation if user has exceeded max_units as per their subscription
    

    # create unit
    unit.is_draft = True
    unit.is_active = False
    unit.is_approved = False  # TODO: add approval logic later

    from repo.units import create_unit
    unit = create_unit(unit)
    from repo.owner import add_unit_to_owner
    add_unit_to_owner(unit.owner_id, unit.id)

    return unit


def submit_unit_for_approval(unit_id: str, ) -> UnitOutAdmin:
    """Submits a draft unit for approval."""
    # find unit by id
    from repo.units import get_unit_by_id
    unit = get_unit_by_id(unit_id)
    # set is_draft to false
    unit.is_draft = False
    # set is_approved to false
    unit.is_approved = False
    # set is_active to false
    unit.is_active = False
    # add approval log
    from models.units import UnitApproval
    # from repo.admin import
    # update unit
    from services.admin import set_approval_status

    approval_status = "pending"
    return set_approval_status(unit_id, approval_status=approval_status,
                               admin_review="Created by owner, awaiting admin review", approval_type="creation")


# class UnitService():
#     def search_units(self, unit_search_filters: UnitSearchFilters, pagination: PaginationIn) -> PaginatedList[UnitOutPublic]:
#         """Searches for units."""
#         pass

#     def get_unit(self, unit_id: str) -> dict:
#         """Gets a unit."""
#         pass

#     def create_unit(self, unit: dict) -> dict:
#         """Creates a unit."""
#         pass

#     def add_unit_image(self, unit_id: str, image: bytes) -> str:
#         """Adds an image to a unit."""
#         pass

#     def add_unit_gallery_link(self, unit_id: str, link: str) -> str:
#         """Adds a gallery link to a unit."""
#         pass

#     def get_owner_units(self, owner_id: str, for_user: RoleEnum, page: PaginationIn) -> PaginatedList[UnitOut]:
#         """Gets all units for an owner."""
#         pass

#     def update_unit(self, unit_id: str, unit: dict) -> dict:
#         """Updates a unit."""
#         pass

#     def delete_unit(self, unit_id: str) -> str:
#         """Deletes a unit."""
#         pass
