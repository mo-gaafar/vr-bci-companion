from models.owner import ProfileOutPublic
from models.common import PaginationOut
from models.units import UnitType
from models.common import DateRange
from fastapi import APIRouter, Depends, HTTPException, Header, Query, Path
from models.units import UnitOutAdmin, UnitOutPublic, UnitBase, UnitApproval, UnitOutPublicDetailed, SearchFilters
from models.common import PaginatedList, PaginationIn, SortQuery
from models.users import UserOut
from util.security import verify_token_header, optional_token_header
from typing import Optional

units = APIRouter(prefix="/units", tags=["units"])


# TODO: GET /units/active - get all active units + pagination

# TODO: GET /units/search - search units + pagination + filters
# TODO: GET /units/{unit_id} - get unit by id
# TODO: GET /units/{unit_id}/ - unit details (exclude detailed booking info)
# ~TODO: GET /units/{unit_id}/reviews - get all reviews for unit
# ~TODO: POST /units/{unit_id}/reviews - create review for unit

# [X] Response Model
# [X] Request Model
# [X] Auth
# [ ] DB
# [ ] Rate Limit & Caching
# [ ] Tests


# @units.get("/", response_model=PaginatedList[UnitOutPublic])
# async def get_all_units(pagination: PaginationIn = Depends(PaginationIn),
#                         sort: Optional[SortQuery] = Depends(SortQuery),
#                         type: Optional[UnitType] = Query(
#                             None, description="Unit Type"),
#                         auth_user: Optional[UserOut] = Depends(
#                             optional_token_header)
#                         ):
#     '''Get all posted units (for public homepage)'''
#     # 501 Not Implemented
#     raise HTTPException(status_code=501, detail="Not Implemented")

# [X] Response Model
# [X] Request Model
# [X] Auth
# [ ] DB
# [ ] Rate Limit & Caching
# [ ] Tests


@units.get("/search", response_model=PaginatedList[UnitOutPublic])
async def search_units(search_filters: SearchFilters = Depends(SearchFilters),
                       date_range: Optional[DateRange] = Depends(DateRange),
                       pagination: PaginationIn = Depends(PaginationIn),
                       sort: Optional[SortQuery] = Depends(SortQuery),
                       auth_user: Optional[UserOut] = Depends(optional_token_header)):
    '''Search units (for public homepage)'''

    from repo.units import get_all_units
    from models.units import UnitPricing, UnitBookingType, GalleryItem, GalleryType

    from repo.units import get_units_filtered
    try:
        units_db_filtered_paginated = get_units_filtered(pagination=pagination, sort=sort, filters=search_filters,
                                                         date_range=date_range, is_active=True)
        pagination_out = units_db_filtered_paginated.pagination
        units = units_db_filtered_paginated.data

        # FIXME refactor this
        public_units = []
        for unit in units:
            if unit.is_active is False:
                continue
            # get min price
            min_price = None
            min_type = None
            min_currency = None

            if search_filters.package is not None:
                for pricing in unit.pricing_list:
                    if pricing.pricing_type == search_filters.package:
                        min_price = pricing.price
                        min_type = pricing.pricing_type
                        min_currency = pricing.currency
                        break
            else:
                for pricing in unit.pricing_list:
                    if min_price is None or pricing.price < min_price:
                        min_price = pricing.price
                        min_type = pricing.pricing_type
                        min_currency = pricing.currency
            if min_price is None:
                min_price = 0
                min_type = UnitBookingType.one_day
                min_currency = "kwd"

            if unit.gallery is not None and len(unit.gallery) > 0:
                thumbnail = unit.gallery[0]
            else:
                thumbnail = GalleryItem(
                    order=0, url="https://jtrepair.com/wp-content/uploads/2019/02/placeholder-image11.jpg", type=GalleryType.image, alt_text="placeholder")

            public_units.append(UnitOutPublic(**unit.dict(), _id=unit.id, starting_price=UnitPricing(
                price=min_price, pricing_type=min_type, currency=min_currency), thumbnail=thumbnail))

        return PaginatedList[UnitOutPublic](data=public_units, pagination=pagination_out)
    except:
        raise HTTPException(
            status_code=404, detail="Error while searching units")

# [X] Response Model
# [X] Request Model
# [X] Auth
# [ ] DB
# [ ] Rate Limit & Caching
# [ ] Tests


@units.get("/{unit_id}/", response_model=UnitOutPublicDetailed)
async def get_unit_details(
        unit_id: str = Path(..., description="Unit ID"),
        auth_user: Optional[UserOut] = Depends(optional_token_header)):
    '''Get unit details by ID (for public)'''
    try:
        from repo.units import get_unit_by_id
        unit = get_unit_by_id(unit_id)
        if unit.is_active:
            from repo.owner import get_owner_by_id
            owner = get_owner_by_id(unit.owner_id)

            unit = UnitOutPublicDetailed(
                **unit.dict(), owner=ProfileOutPublic(_id=owner.id, **owner.contact.dict()), _id=unit.id)
            return unit
        else:
            raise HTTPException(
                status_code=404, detail="Unit not active")
    except:
        raise HTTPException(status_code=404, detail="Unit not found")

# Getter for available locations (cities) for a certain country


# @units.get("/{unit_id}/reviews")
# async def get_unit_reviews():
#     # 501 Not Implemented
    # raise HTTPException(status_code=501, detail="Not Implemented")

# @units.post("/{unit_id}/reviews")
# async def create_unit_review():
#     # 501 Not Implemented
    # raise HTTPException(status_code=501, detail="Not Implemented")
