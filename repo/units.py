

from datetime import datetime
from models.units import BlockedDate
from models.common import SortBy, SortOrder
from models.common import DateRange
from models.units import UnitOutPublicDetailed, UnitOutPublic, SearchFilters,  UnitOutPublicDetailed
from models.common import PaginationIn, PaginationOut, PaginatedList, SortQuery
from typing import Optional, List
from typing import Optional
from models.units import GalleryType
from models.units import UnitPricing, UnitBookingType
from models.common import PaginationIn, PaginationOut, PaginatedList
from models.units import UnitInDB, UnitOutAdmin
from util.misc import db_to_dict
from abc import ABC, abstractmethod
from models.units import GalleryItem, UnitOutPublic
from repo.db import MongoDB
from bson import ObjectId


def sort_gallery(unit_id: str) -> list[GalleryItem]:
    # reorganize gallery
    MongoDB.units.update_one({"_id": ObjectId(unit_id)}, {
        "$set": {"gallery": sorted(MongoDB.units.find_one({"_id": ObjectId(unit_id)})["gallery"], key=lambda x: x["order"])}
    })


def update_blocked_dates(unit_id: str, blocked_dates: List[BlockedDate]) -> bool:
    """Updates the blocked dates for a unit."""
    if MongoDB.units.find_one({"_id": ObjectId(unit_id)}) is None:
        return False
    MongoDB.units.update_one({"_id": ObjectId(unit_id)}, {
        "$set": {"blocked_list": [blocked_date.dict() for blocked_date in blocked_dates]}
    })
    return True


def add_gallery_item_to_unit(unit_id: str, gallery_item: GalleryItem) -> GalleryItem:
    # push image to unit (based on order)
    MongoDB.units.update_one({"_id": ObjectId(unit_id)}, {
        "$push": {"gallery": gallery_item.dict()}
    })
    # reorganize gallery
    sort_gallery(unit_id)
    pass


def create_unit(unit: UnitInDB) -> UnitOutAdmin:
    # create unit
    unit_id = MongoDB.units.insert_one(unit.dict()).inserted_id
    unit = MongoDB.units.find_one({"_id": ObjectId(unit_id)})
    return UnitOutAdmin(**db_to_dict(unit))


def get_unit_by_id(unit_id: str) -> Optional[UnitInDB]:
    """Gets a unit by its ID."""
    unit = MongoDB.units.find_one({"_id": ObjectId(unit_id)})
    if unit is None:
        return None
    return UnitInDB(**db_to_dict(unit))


def get_all_units(pagination: Optional[PaginationIn] = None,
                  subscribed_only: Optional[bool] = True,
                  is_active: Optional[bool] = True,
                  ) -> PaginatedList[UnitInDB]:
    """Gets all units."""
    if pagination is None:
        units = MongoDB.units.find()
        return [UnitInDB(**db_to_dict(unit)) for unit in units]

    # TODO: this should be in service layer
    filter = {}
    if subscribed_only:
        # CHECK IF OWNER NOT IN THE FOLLOWING LIST
        from repo.owner import get_all_unsubscribed_owners
        unsubscribed_owners = get_all_unsubscribed_owners()
        filter["owner_id"] = {
            "$nin": [owner.id for owner in unsubscribed_owners]}
    if is_active:
        filter["is_active"] = is_active

    units = MongoDB.units.find(filter).skip(
        (pagination.page-1)*pagination.limit).limit(pagination.limit)
    units = [UnitInDB(**db_to_dict(unit)) for unit in units]
    total = MongoDB.units.count_documents({})
    return PaginatedList[UnitInDB](data=units, pagination=PaginationOut(page=pagination.page, num_items=pagination.limit, total=total))


def get_min_pricing(unit_pricing: Optional[list[UnitPricing]] = None) -> UnitPricing:
    """Gets the minimum pricing from a list of pricings."""
    min_price = None
    min_type = None
    min_currency = None
    if unit_pricing is None:
        return UnitPricing(price=0, pricing_type=UnitBookingType.one_day, currency="kwd")
    for pricing in unit_pricing:
        if min_price is None or pricing.price < min_price:
            min_price = pricing.price
            min_type = pricing.pricing_type
            min_currency = pricing.currency
    if min_price is None:
        min_price = 0
        min_type = UnitBookingType.one_day
        min_currency = "kwd"
    return UnitPricing(
        price=min_price, pricing_type=min_type, currency=min_currency)


def unitindb_to_unitoutadmin(unit) -> UnitOutAdmin:
    '''Mapping from UnitInDB to UnitOutPublic'''
    unit_db = UnitInDB(**db_to_dict(unit))
    thumb = GalleryItem(
        order=0, url="https://jtrepair.com/wp-content/uploads/2019/02/placeholder-image11.jpg", type=GalleryType.image, alt_text="placeholder")
    if len(unit_db.gallery) > 0:
        thumb = unit_db.gallery[0]

    return UnitOutAdmin(**unit_db.dict(), _id=unit_db.id,  thumbnail=thumb, starting_price=get_min_pricing(unit_db.pricing_list))


def unitoutadmin_to_unitoutpublic(unit: UnitOutAdmin) -> UnitOutPublic:
    '''Mapping from UnitOutAdmin to UnitOutPublic'''
    starting_price = get_min_pricing(unit.pricing_list)
    thumbnail = GalleryItem(
        order=0, url="https://jtrepair.com/wp-content/uploads/2019/02/placeholder-image11.jpg", type=GalleryType.image, alt_text="placeholder")
    if len(unit.gallery) > 0:
        thumbnail = unit.gallery[0]
    return UnitOutPublic(**unit.dict(), _id=unit.id, thumbnail=thumbnail, starting_price=starting_price)


def get_all_owner_units(owner_id: str, pagination: Optional[PaginationIn] = None, ) -> PaginatedList[UnitOutAdmin]:
    """Gets all units for an owner. with pagination"""

    if pagination is None:
        units = MongoDB.units.find({"owner_id": owner_id})
        pagination = PaginationIn(page=1, limit=1000)

    else:
        units = MongoDB.units.find({"owner_id": owner_id}).skip(
            (pagination.page-1)*pagination.limit).limit(pagination.limit)

    units = [unitindb_to_unitoutadmin(unit) for unit in units]
    total = MongoDB.units.count_documents({"owner_id": owner_id})

    return PaginatedList[UnitOutAdmin](data=units, pagination=PaginationOut(page=pagination.page, num_items=pagination.limit, total=total, total_pages=total//pagination.limit))


def get_units_filtered(pagination: Optional[PaginationIn] = None, sort: Optional[SortQuery] = None, filters: Optional[SearchFilters] = None, date_range: Optional[DateRange] = None, is_active: Optional[bool] = True,
                       check_owner_subscribed: Optional[bool] = True) -> PaginatedList[UnitInDB]:
    """Gets all units filtered by filters and sorted by sort."""
    query = {}
    if check_owner_subscribed:
        # CHECK IF OWNER NOT IN THE FOLLOWING LIST
        from repo.owner import get_all_unsubscribed_owners
        unsubscribed_owners = get_all_unsubscribed_owners()
        query["owner_id"] = {
            "$nin": [owner.id for owner in unsubscribed_owners]}
    if is_active is not None:
        query["is_active"] = is_active

    if filters.keywords is not None:
        query["$text"] = {"$search": filters.keywords}

    if date_range is not None:
        # # check the date range array for any date that is in the range if true then exclude the unit
        # query["booked_list"] = {
        #     "$not": {"$elemMatch": {"check_in_date": {"$lte": date_range.end}, "check_out_date": {"$gte": date_range.start}}}}
        # # TODO: check for blocked dates too?
        # query["blocked_dates"] = {
        #     "$not": {"$elemMatch": {"start_date": {"$lte": date_range.end}, "end_date": {"$gte": date_range.start}}}}

        # if date_range is not None:
        #     query["booked_list"] = {
        #         "$or": [
        #             {
        #                 "$and": [
        #                     {"check_in_date": {
        #                         "$gte": date_range.end}},
        #                     {"check_out_date": {
        #                         "$lte": date_range.start}}
        #                 ]
        #             },
        #             {
        #                 "$and": [
        #                     {"check_in_date": {
        #                         "$lte": date_range.start}},
        #                     {"check_out_date": {
        #                         "$gte": date_range.end}}
        #                 ]
        #             },
        #             {
        #                 "$and": [
        #                     {"check_in_date": {
        #                         "$lte": date_range.end}},
        #                     {"check_out_date": {
        #                         "$gte": date_range.start}}
        #                 ]
        #             }
        #         ]
        #     }

        #     query["blocked_dates"] = {
        #         "$or": [
        #             {
        #                 "$and": [
        #                     {"start_date": {"$gte": date_range.end}},
        #                     {"end_date": {"$lte": date_range.start}}
        #                 ]
        #             },
        #             {
        #                 "$and": [
        #                     {"start_date": {
        #                         "$lte": date_range.start}},
        #                     {"end_date": {"$gte": date_range.end}}
        #                 ]
        #             },
        #             {
        #                 "$and": [
        #                     {"start_date": {"$lte": date_range.end}},
        #                     {"end_date": {"$gte": date_range.start}}
        #                 ]
        #             }
        #         ]
        #     }
        pass

    if filters is not None:
        # TODO: Filter by country

        if filters.city is not None:
            # check if city is in the list of cities
            # look for match in location.address array of dicts where level is city and name is the city name
            query["location.address"] = {
                "$elemMatch": {"level": "city", "name": filters.city}}
        if filters.package is not None:
            # check if package is in the list of packages
            query["pricing_list"] = {
                "$elemMatch": {"pricing_type": filters.package}}

        if filters.unit_type is not None:
            query["type"] = filters.unit_type
        # amenities filtering
        if filters.num_bathrooms is not None:
            # morethan or equal
            query["amenities.num_bathrooms"] = {
                "$gte": filters.num_bathrooms}
        if filters.num_master_bedrooms is not None:
            query["amenities.num_master_bedrooms"] = {
                "$gte": filters.num_master_bedrooms}
        if filters.num_single_bedrooms is not None:
            query["amenities.num_single_bedrooms"] = {
                "$gte": filters.num_single_bedrooms}
        if filters.num_shared_pool is not None:
            query["amenities.num_public_pools"] = {
                "$gte": filters.num_shared_pool}
        if filters.num_private_pool is not None:
            query["amenities.num_private_pools"] = {
                "$gte": filters.num_private_pool}
        if filters.num_floors is not None:
            query["amenities.levels"] = {
                "$gte": filters.num_floors}
        if filters.num_living_rooms is not None:
            query["amenities.num_living_rooms"] = {
                "$gte": filters.num_living_rooms}

        if filters.sea_nearby is not None:
            query["amenities.sea_nearby"] = filters.sea_nearby
        if filters.garden is not None:
            query["amenities.garden"] = filters.garden
        if filters.elevator is not None:
            query["amenities.elevator"] = filters.elevator
        if filters.driver_room is not None:
            query["amenities.driver_room"] = filters.driver_room
        if filters.nanny_room is not None:
            query["amenities.nanny_room"] = filters.nanny_room
        if filters.suitable_for_elderly_disabled is not None:
            query["amenities.elderly_disabled_suitable"] = filters.suitable_for_elderly_disabled
        if filters.wifi is not None:
            query["amenities.wifi"] = filters.wifi
        # TODO: add more filters?

    units = MongoDB.units.find(query)
    # TODO: Add sorting functionality

    if sort is not None:
        if sort.sort_by == SortBy.relevance:
            key_or_list = []
            if filters.keywords is not None:
                key_or_list.append(("score", {"$meta": "textScore"}))
            else:
                key_or_list.append(("created_at", -1))
        elif sort.sort_by == SortBy.name:
            if sort.sort_order == SortOrder.asc:
                key_or_list = [("name", 1)]
            elif sort.sort_order == SortOrder.desc:
                key_or_list = [("name", -1)]
        # elif sort.sort_by == SortBy.popularity:
        elif sort.sort_by == SortBy.price:
            # sort by least price in pricing_list
            if sort.sort_order == SortOrder.asc:
                key_or_list = [("pricing_list.price", 1)]
            elif sort.sort_order == SortOrder.desc:
                key_or_list = [("pricing_list.price", -1)]
        elif sort.sort_by == SortBy.time_created:
            if sort.sort_order == SortOrder.asc:
                key_or_list = [("created_at", 1)]
            elif sort.sort_order == SortOrder.desc:
                key_or_list = [("created_at", -1)]
        else:
            key_or_list = [("created_at", -1)]

    if pagination is not None:
        units = units.skip(
            (pagination.page-1)*pagination.limit).limit(pagination.limit).sort(key_or_list)
    units = [UnitInDB(**db_to_dict(unit)) for unit in units]
    total = MongoDB.units.count_documents(query)
    return PaginatedList[UnitInDB](data=units, pagination=PaginationOut(page=pagination.page, num_items=pagination.limit, total=total, total_pages=total//pagination.limit))


def soft_delete_unit(unit_id: str):
    """Sets a unit's is_active to False."""
    if MongoDB.units.find_one({"_id": ObjectId(unit_id)}) is None:
        return False
    MongoDB.units.update_one({"_id": ObjectId(unit_id)}, {
        "$set": {"is_active": False}
    })
    return True


def hard_delete_unit(unit_id: str):
    unit = MongoDB.units.find_one({"_id": ObjectId(unit_id)})
    if unit is None:
        return False

    """Deletes a unit by its ID."""
    MongoDB.units.delete_one({"_id": ObjectId(unit_id)})
    # delete all bookings for this unit
    MongoDB.bookings.delete_many({"unit_id": unit_id})
    # delete from user's owned_units_id
    MongoDB.owner.update_many({}, {"$pull": {"owned_units_id": unit_id}})

    return True


def get_units_by_ids(unit_ids: list[str]) -> list[UnitInDB]:
    """Gets a list of units by their IDs."""
    units = MongoDB.units.find(
        {"_id": {"$in": [ObjectId(unit_id) for unit_id in unit_ids]}})
    return [UnitInDB(**db_to_dict(unit)) for unit in units]
