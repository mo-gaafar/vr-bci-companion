from util.security import verify_token_header, access_check
from fastapi import Depends
from models.users import UserOut
from repository.tickets import update_foodstuff_amenity
from models.amenities import FoodstuffScanOut
from models.business import Venue
from repository.business import get_venue
from repository.tickets import get_tickets_in_venue
from repository.tickets import get_ticket_by_id
from models.amenities import CheckInCar, ParkingScanOut
from datetime import datetime
from models.amenities import FoodstuffAmenity, ParkingAmenity, Amenities, AmenityType
from bson.objectid import ObjectId
from models.amenities import VenueParkingSummary
from util.multitenant import get_tenant_db
from fastapi import APIRouter, Query, Header, HTTPException

from typing import Optional

from models.tickets import GuestInList, GuestTicketDetails, Ticket, ScanOut

amenities = APIRouter(tags=["amenities"])

# add amenitiest to ticket tiers


# @amenities.post('/foodstuff/add/{ticket_tier_id}', tags=['amenities'])
# async def foodstuff_add(ticket_tier_id: str, tenant_id: str = Header(...), auth_user: UserOut = Depends(verify_token_header), add_to_old_tickets: bool = False):
#     """Add foodstuff to ticket tier"""
#     # [ ] check if tickettier exists
#     # TODO: add functionality to add foodstuff to old tickets
#     # [ ] check if ticket is valid and exists
#     # [ ] check if ticket contains foodstuff amenity already
#     # [ ] add foodstuff amenity to ticket
#     pass


# @amenities.patch('/parking/edit/{ticket_tier_id}', tags=['amenities'])
# async def parking_edit(ticket_tier_id: str, tenant_id: str = Header(...), auth_user: UserOut = Depends(verify_token_header), add_to_old_tickets: bool = False):
#     '''Edit parking details for ticket tier'''
#     # [ ] check if tickettier exists
#     pass


# DONE NEEDS TESTING
@amenities.post('/parking/scan/{ticket_id}', tags=['amenities'], response_model=ParkingScanOut)
async def parking_scan(ticket_id: str, tenant_id: str = Header(...), auth_user: UserOut = Depends(verify_token_header), is_check_in: Optional[bool] = Query(None)):
    """Parking attendant scans ticket and returns car to customer"""
    # [ ] check if ticket is valid and exists
    # [ ] check if ticket contains parking amenity or quantity_used is less than quantity_allowed
    # [ ] update quantity_used and scan_history
    # [ ] return parking details
    # [ ] add to used slots in venue model
    db = get_tenant_db(tenant_id, precheck=True)
    ticket = get_ticket_by_id(db, ticket_id)
    venue = get_venue(db, ticket.venue_id)
    if ticket.amenities is None:
        raise HTTPException(
            status_code=404, detail="Ticket does not contain any amenities")
    if ticket.amenities.parking is None:
        raise HTTPException(
            status_code=404, detail="Ticket does not contain any parking")

    if ticket.amenities.parking.scan_history is None:
        ticket.amenities.parking.scan_history = []
    if is_check_in is None:
        if len(ticket.amenities.parking.scan_history) == 0:
            is_check_in = True
        else:
            is_check_in = not ticket.amenities.parking.scan_history[-1].is_checkin

    if is_check_in is True:
        # check if venue not at maximum capacity after this check in
        if venue.parking_used_slots + 1 >= venue.parking_limit:
            raise HTTPException(
                status_code=404, detail=f"Venue is at maximum parking capacity")

        if ticket.amenities.parking.quantity_used >= ticket.amenities.parking.quantity_allowed:
            raise HTTPException(
                status_code=404, detail=f"This ticket is not allowed to park more than {ticket.amenities.parking.quantity_allowed} cars")

        ticket.amenities.parking.quantity_used = ticket.amenities.parking.quantity_used + 1
        # TODO: add scanner id
        ticket.amenities.parking.scan_history.append(
            CheckInCar(timestamp=datetime.utcnow(), is_checkin=True))

        # TODO: update venue used slots
        db.venues.update_one({"_id": ObjectId(ticket.venue_id)}, {
            "$inc": {"parking_used_slots": 1}})
    else:
        # check if this check out has had a check in before it
        if len(ticket.amenities.parking.scan_history) == 0:
            raise HTTPException(
                status_code=404, detail="This ticket has not been checked in before")
        # check if this check out is the latest entry after

        ticket.amenities.parking.quantity_used = ticket.amenities.parking.quantity_used - 1
        ticket.amenities.parking.scan_history.append(
            CheckInCar(timestamp=datetime.utcnow(), is_checkin=False))

        db.venues.update_one({"_id": ObjectId(ticket.venue_id)}, {
            "$inc": {"parking_used_slots": -1}})

    db.tickets.update_one({"_id": ObjectId(ticket_id)}, {
        "$set": {"amenities.parking": ticket.amenities.parking.dict()}})

    return get_post_parking_scan_summary(db, ticket_id, ticket.venue_id)


def get_amenities_post_scan_message(scan_history):
    if len(scan_history) == 0:
        return "No scan history found"
    if scan_history[-1].is_checkin is True:
        return "Check in successful"
    else:
        return "Check out successful"


def get_post_parking_scan_summary(db, ticket_id, venue_id) -> ParkingScanOut:
    # get ticket
    # get venue
    # get parking amenity
    ticket = get_ticket_by_id(db, ticket_id)
    venue = get_venue(db, venue_id)
    parking_amenity = ticket.amenities.parking
    if parking_amenity is None:
        raise HTTPException(
            status_code=404, detail="Ticket does not contain any parking")

    if parking_amenity.scan_history is None:
        parking_amenity.scan_history = []

    # get last checkin if it is the latest entry then set it as entry time
    # if last checkin is not the latest entry then set it as exit time and set entry time as the entry before it
    if len(parking_amenity.scan_history) == 0:
        # raise HTTPException(
        #     status_code=404, detail="Parking scan history is empty")
        entry_time = None
        exit_time = None
    elif len(parking_amenity.scan_history) == 1:
        entry_time = parking_amenity.scan_history[0].timestamp
        exit_time = None
    else:
        if parking_amenity.scan_history[-1].is_checkin is True:
            entry_time = parking_amenity.scan_history[-1].timestamp
            exit_time = None
        else:
            entry_time = parking_amenity.scan_history[-2].timestamp
            exit_time = parking_amenity.scan_history[-1].timestamp

    duration_min = 0
    if entry_time is not None and exit_time is not None:
        duration_min = int((exit_time - entry_time).total_seconds() // 60)

    remaining_parking_uses = parking_amenity.quantity_allowed - \
        parking_amenity.quantity_used

    return ParkingScanOut(guest_details=ticket.guest_details,
                          duration_min=duration_min, plate_number="N/A", message=get_amenities_post_scan_message(parking_amenity.scan_history),
                          entry_price=0, entry_time=entry_time, exit_time=exit_time, parking_amenity=ticket.amenities.parking,
                          remaning_spaces=venue.parking_limit - venue.parking_used_slots, remaining_parking_uses=remaining_parking_uses)


@amenities.post('/foodstuff/scan/{ticket_id}', tags=['amenities'], response_model=FoodstuffScanOut)
async def foodstuff_scan(ticket_id: str, tenant_id: str = Header(...), amenity_id: str = Query(...), auth_user: UserOut = Depends(verify_token_header)):
    """Barista scans ticket and returns foodstuff to customer"""
    # [x] check if ticket is valid and exists
    # [x] check if ticket contains foodstuff amenity
    # [x] update quantity_used and scan_history
    # [x] return foodstuff details

    db = get_tenant_db(tenant_id, precheck=True)
    ticket = get_ticket_by_id(db, ticket_id)
    if ticket.amenities is None:
        raise HTTPException(
            status_code=404, detail="Ticket does not contain any amenities")
    if ticket.amenities.foodstuff is None:
        raise HTTPException(
            status_code=404, detail="Ticket does not contain any foodstuff")

    # find amenity id in foodstuff
    foodstuff = None
    for food in ticket.amenities.foodstuff:
        if food.id == amenity_id:
            foodstuff = food
            break

    if foodstuff is None:
        raise HTTPException(
            status_code=404, detail=f"Foodstuff amenity with id {amenity_id} not found")

    if foodstuff.quantity_used >= foodstuff.quantity_allowed:
        raise HTTPException(
            status_code=404, detail=f"This ticket is not allowed to use more than {foodstuff.quantity_allowed} {foodstuff.name}")

    foodstuff.quantity_used = foodstuff.quantity_used + 1
    foodstuff.scan_history.append(
        CheckInCar(timestamp=datetime.utcnow(), is_checkin=True))

    update_foodstuff_amenity(db, ticket_id, foodstuff)

    return get_post_food_scan_summary(db, ticket_id, ticket.venue_id, amenity_id)


def get_post_food_scan_summary(db, ticket_id, venue_id, foodstuff_id):
    ticket = get_ticket_by_id(db, ticket_id)
    venue = get_venue(db, venue_id)
    if ticket.amenities is None:
        raise HTTPException(
            status_code=404, detail="Ticket does not contain any amenities")
    if ticket.amenities.foodstuff is None:
        raise HTTPException(
            status_code=404, detail="Ticket does not contain any foodstuff")

    foodstuff = ticket.amenities.foodstuff
    if len(foodstuff) == 0:
        raise HTTPException(
            status_code=404, detail="Foodstuff scan history is empty")

    if foodstuff_id is not None:
        selected_food = None
        for food in foodstuff:
            if food.id == foodstuff_id:
                selected_food = food
                break
        if selected_food is None:
            raise HTTPException(
                status_code=404, detail=f"Foodstuff amenity with id {foodstuff_id} not found")

        remaning_uses = selected_food.quantity_allowed - selected_food.quantity_used
    else:
        selected_food = None
        remaning_uses = 0

    allowed_foodstuff = []
    for food in foodstuff:
        # check if quantity used is less than quantity allowed
        if food.quantity_used < food.quantity_allowed:
            allowed_foodstuff.append(food)

    message = ""
    if selected_food is not None:
        if len(selected_food.scan_history) == 0:
            message = "No scan history found"
        elif selected_food.scan_history[-1].is_checkin is True:
            message = "Coupon redeemed successfully, remaining uses: " + \
                str(remaning_uses)

    return FoodstuffScanOut(guest_details=ticket.guest_details,
                            selected_food=selected_food, message=message,
                            remaining_uses=remaning_uses,
                            amenities_list=ticket.amenities.foodstuff, allowed_foodstuff=allowed_foodstuff)


@amenities.get('/parking/info/{ticket_id}', tags=['amenities'], response_model=ParkingScanOut)
async def parking_info(ticket_id: str, tenant_id: str = Header(...), auth_user: UserOut = Depends(verify_token_header)):
    """Parking attendant scans ticket and returns car to customer"""
    # [ ] check if ticket is valid and exists
    # [ ] check if ticket contains parking amenity
    # [ ] return parking details
    db = get_tenant_db(tenant_id, precheck=True)
    ticket = get_ticket_by_id(db, ticket_id)
    if ticket.amenities is None:
        raise HTTPException(
            status_code=404, detail="Ticket does not contain any amenities")
    if ticket.amenities.parking is None:
        raise HTTPException(
            status_code=404, detail="Ticket does not contain any parking")

    if ticket.amenities.parking.scan_history is None:
        ticket.amenities.parking.scan_history = []

    return get_post_parking_scan_summary(db, ticket_id, ticket.venue_id)


@amenities.get('/foodstuff/info/{ticket_id}', tags=['amenities'], response_model=FoodstuffScanOut)
async def foodstuff_info(ticket_id: str, tenant_id: str = Header(...), auth_user: UserOut = Depends(verify_token_header)):
    """Parking attendant scans ticket and returns car to customer"""
    # [ ] check if ticket is valid and exists
    # [ ] check if ticket contains foodstuff amenity
    # [ ] return foodstuff details
    db = get_tenant_db(tenant_id, precheck=True)
    ticket = get_ticket_by_id(db, ticket_id)
    if ticket.amenities is None:
        raise HTTPException(
            status_code=404, detail="Ticket does not contain any amenities")
    if ticket.amenities.foodstuff is None:
        raise HTTPException(
            status_code=404, detail="Ticket does not contain any foodstuff")
    # TODO: more userful summarized response?
    return get_post_food_scan_summary(db, ticket_id, ticket.venue_id, None)


@amenities.get('/venue/parking/summary/{venue_id}', tags=['amenities', 'dashboard'], response_model=VenueParkingSummary)
async def venue_parking_summary(venue_id: str, tenant_id: str = Header(...), auth_user: UserOut = Depends(verify_token_header)):
    """Returns parking details for venue"""
    # [x] check if venue exists
    # [x] loop over all tickets and check if they contain parking amenity
    # [x] summarize parking details
    db = get_tenant_db(tenant_id, precheck=True)
    tickets = get_tickets_in_venue(db, venue_id)
    venue = get_venue(db, venue_id)

    if venue.parking_limit is None:
        raise HTTPException(
            status_code=404, detail="Venue parking limit not found")

    parking_tickets = []
    total_parked_cars = 0
    total_parked_mins = 0
    for ticket in tickets:
        if ticket.amenities is not None:
            if ticket.amenities.parking is not None:
                parking_tickets.append(ticket)
                n_parked, parked_mins = get_parking_from_scan_history(ticket)
                total_parked_cars = total_parked_cars + n_parked
                total_parked_mins = total_parked_mins + parked_mins
    avg_parking_duration = 0
    if total_parked_cars != 0:
        avg_parking_duration = total_parked_mins // total_parked_cars
    return VenueParkingSummary(total_parked_cars=total_parked_cars, max_parking_capacity=venue.parking_limit,
                               remaining_parking_capacity=venue.parking_limit - total_parked_cars,
                               total_parking_durartion_min=total_parked_mins, average_parking_duration_min=avg_parking_duration)


def get_parking_from_scan_history(ticket: Ticket):
    """Returns True if guest is parked
    Returns:
        parked_count: int
        parked_mins: int
    """
    parked_count = 0
    parked_mins = 0
    check_in = None
    if ticket.amenities is not None:
        if ticket.amenities.parking is not None:
            if ticket.amenities.parking.scan_history is not None:
                for scan in ticket.amenities.parking.scan_history:
                    # count checkins that are not checked out
                    if scan.is_checkin is True:
                        parked_count = parked_count + 1
                        check_in = scan.timestamp
                    else:
                        parked_count = parked_count - 1
                        check_out = scan.timestamp
                        if check_in is not None:
                            parked_mins = parked_mins + \
                                (check_out - check_in).total_seconds() // 60

    return parked_count, int(parked_mins)


def refresh_venue_parking(venue_id, tenant_id):
    """Refreshes venue parking counter and returns it"""
    db = get_tenant_db(tenant_id, precheck=True)
    tickets = get_tickets_in_venue(db, venue_id)
    venue = get_venue(db, venue_id)

    venue.parking_used_slots = 0
    for ticket in tickets:
        if ticket.amenities is not None:
            if ticket.amenities.parking is not None:
                n_parked, parked_mins = get_parking_from_scan_history(ticket)
                venue.parking_used_slots = venue.parking_used_slots + n_parked

    db.venues.update_one({"_id": ObjectId(venue_id)}, {
        "$set": {"parking_used_slots": venue.parking_used_slots}}, upsert=True)

    return venue.parking_used_slots

# @amenities.get('/venue/foodstuff/summary/{venue_id}', tags=['amenities', 'dashboard'])
# async def venue_foodstuff_summary(venue_id: str, tenant_id: str = Header(...), auth_user: UserOut = Depends(verify_token_header)):
#     """Returns foodstuff details for venue"""
#     # [ ] check if venue exists
#     # [ ] loop over all tickets and check if they contain foodstuff amenity
#     # [ ] summarize foodstuff details
#     pass
