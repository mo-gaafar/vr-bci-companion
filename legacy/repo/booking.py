from models.units import BookingInUnit
from models.common import PaginationOut
from typing import Optional
from repo.customer import get_customer_by_id
from repo.owner import get_owner_by_id
from repo.units import get_unit_by_id
from models.booking import BookingStatus
from abc import ABC, abstractmethod

from models.customer import CustomerInDB
from pymongo import MongoClient
from models.common import PaginationIn, PaginatedList
from repo.db import MongoDB
from bson import ObjectId

from models.booking import BookingInDB, BookingCreate, UnitBookingType
from models.units import UnitInDB
from models.owner import OwnerInDB
from models.customer import CustomerInDB
from models.common import Currency
from util.misc import db_to_dict
from datetime import datetime, timedelta

#! THIS NEEDS REFACTORING TO SERVICES AND UTILS


def check_booking_overlap(unit: UnitInDB, check_in_date: datetime, check_out_date: datetime):
    # check if dates do not overlap with "booked_list"
    booked_list = unit.booked_list
    for booking in booked_list:
        # check if check_in_date is between start_date and end_date
        # ! Note!! This assumes that all the bookings in unit are approved bookings only
        if (
            booking.check_in_date.replace(tzinfo=None) <= check_in_date.replace(
                tzinfo=None) <= booking.check_out_date.replace(tzinfo=None)
            or booking.check_in_date.replace(tzinfo=None) <= check_out_date.replace(tzinfo=None) <= booking.check_out_date.replace(tzinfo=None)
            or (check_in_date.replace(tzinfo=None) <= booking.check_in_date.replace(tzinfo=None) and check_out_date.replace(tzinfo=None) >= booking.check_out_date.replace(tzinfo=None))
        ):
            # Dates overlap, return True or handle the overlap as needed
            raise Exception(
                "Booking dates overlap with existing booking, please choose another convenient timing. \n  تاريخ الحجز يتداخل مع حجز موجود، رجاءً اختيار توقيت اخر")
    # query all pending bookings in booking range and check for overlap too
    bookings = MongoDB.bookings.find({
        "unit_id": ObjectId(unit.id),
        "$or": [
            {
                "status": BookingStatus.pending
            },
            {
                "status": BookingStatus.confirmed
            }

        ],
        "$or": [
            {
                "$and": [
                    {"check_in_date": {"$lte": check_in_date}},
                    {"check_out_date": {"$gte": check_in_date}}
                ]
            },
            {
                "$and": [
                    {"check_in_date": {"$lte": check_out_date}},
                    {"check_out_date": {"$gte": check_out_date}}
                ]
            }
        ]
    })
    # check if there are any results in cursor
    if bookings.retrieved > 0:
        raise Exception("Booking dates overlap with existing booking")


def check_blocked_dates(unit: UnitInDB, check_in_date: datetime, check_out_date: datetime):
    # check if dates do not overlap with "blocked_list" or "booked_list"
    blocked_list = unit.blocked_list
    for blocked_date in blocked_list:
        # # blocked date can be a repeating interval
        # # check if check_in_date is between start_date and end_date accounting for repeating interval
        # if blocked_date.recurring_times > 0:
        #     # get the nearest neighbor of check_in_date if exists
        #     delta = check_in_date - blocked_date.start_date
        #     # if delta is negative, then check_in_date is before start_date
        #     if delta.days < 0:
        #         continue
        #     # else check if delta is a multiple of interval_days and adjust it

        # check if check_in_date does not overlap with blocked_date
        if blocked_date.start_date <= check_in_date.replace(tzinfo=None) <= blocked_date.end_date:
            raise Exception(
                "Booking Failed: Your check in date is blocked by owner")
        # check if check_out_date does not overlap with blocked_date
        if blocked_date.start_date <= check_out_date.replace(tzinfo=None) <= blocked_date.end_date:
            raise Exception(
                "Booking Failed: Your check in date is blocked by owner")
        # check if blocked_date is between check_in_date and check_out_date
        if check_in_date.replace(tzinfo=None) <= blocked_date.start_date.replace(tzinfo=None) <= check_out_date.replace(tzinfo=None):
            raise Exception(
                "Booking Failed: Your check in date is blocked by owner")
        if check_in_date.replace(tzinfo=None) <= blocked_date.end_date.replace(tzinfo=None) <= check_out_date.replace(tzinfo=None):
            raise Exception(
                "Booking Failed: Your check in date is blocked by owner")

    # TODO: implement this for recurring timings too


def get_booking_price(unit: UnitInDB, booking_type: UnitBookingType, currency: Currency, check_in_date: datetime, check_out_date: datetime):
    pricing_list = unit.pricing_list
    pricing = None
    # search for price in the same currency in pricing_list
    for pricing in pricing_list:
        if pricing.pricing_type == booking_type and pricing.currency == currency:
            return pricing

    if pricing is None:
        raise Exception("Pricing unavailable for this selection")


def get_check_out_date(booking_type: UnitBookingType, check_in_date: datetime):
    if booking_type == UnitBookingType.one_day:
        return check_in_date + timedelta(days=1)
    elif booking_type == UnitBookingType.one_week:
        return check_in_date + timedelta(days=7)
    elif booking_type == UnitBookingType.one_month:
        return check_in_date + timedelta(days=30)
    elif booking_type == UnitBookingType.sunday_to_wednesday:
        # get the next sunday
        if check_in_date.weekday() == 6:
            return check_in_date + timedelta(days=3)
        else:
            raise Exception(
                "Check in date is not a sunday \n  يوم الوصول ليس يوم أحد")
    elif booking_type == UnitBookingType.thursday_to_saturday:
        # get the next thursday
        if check_in_date.weekday() == 3:
            return check_in_date + timedelta(days=3)
        else:
            raise Exception(
                "Check in date is not a thursday \n  يوم الوصول ليس يوم خميس")


def create_booking(booking_create: BookingCreate):
    # check if unit exists
    unit = get_unit_by_id(booking_create.unit_id)
    if unit is None:
        raise Exception("Unit not found \n الوحدة غير موجودة")
    if unit.is_active == False:
        raise Exception("Unit is not active \n الوحدة غير مفعلة")
    # check if unit owner exists
    owner = get_owner_by_id(unit.owner_id)
    if owner is None:
        raise Exception("Owner not found \n المالك غير موجود")
    if owner.subscription_end_date is None:
        raise Exception(
            "Owner has no subscription, this unit cannot be booked \n المالك ليس لديه اشتراك ، لا يمكن حجز هذه الوحدة")
    if owner.subscription_end_date < datetime.utcnow():
        raise Exception(
            "Owner subscription has expired \n انتهى اشتراك المالك")
    # check if customer exists
    customer = get_customer_by_id(booking_create.customer_id)
    if customer is None:
        raise Exception("Customer not found \n العميل غير موجود")

    # check if date is in the future
    if booking_create.check_in_date.replace(tzinfo=None) < datetime.utcnow() or booking_create.check_out_date.replace(tzinfo=None) < datetime.utcnow():
        raise Exception("Booking date is in the past \n تاريخ الحجز في الماضي")

    # fix date of check_out based on booking_type and check_in_date
    booking_create.check_out_date = get_check_out_date(
        booking_create.booking_type, booking_create.check_in_date)

    # check if dates do not overlap with "blocked_list" or "booked_list"
    check_booking_overlap(unit, booking_create.check_in_date,
                          booking_create.check_out_date)

    check_blocked_dates(unit, booking_create.check_in_date,
                        booking_create.check_out_date)

    # calculate price
    #! currency is hardcoded to kwd for now
    pricing = get_booking_price(unit, booking_create.booking_type, "kwd",
                                booking_create.check_in_date, booking_create.check_out_date)

    # create booking in db
    booking_indb = BookingInDB(
        **booking_create.dict(), price=pricing.price, currency=pricing.currency, status=BookingStatus.pending, owner_id=owner.id)
    booking_id = MongoDB.booking.insert_one(
        booking_indb.dict()).inserted_id
    booking_indb.id = str(booking_id)

    return booking_indb


def get_booking_by_id(booking_id: str) -> BookingInDB:
    booking = MongoDB.booking.find_one({"_id": ObjectId(booking_id)})
    if booking is None:
        return None
    return BookingInDB(**db_to_dict(booking))


def insert_booking(booking: BookingInDB):
    booking_id = MongoDB.booking.insert_one(
        booking.dict()).inserted_id
    booking.id = str(booking_id)
    return booking


def clear_pending_bookings(unit_id, check_in_date, check_out_date):
    # clear all pending bookings in the same time frame
    MongoDB.booking.update_many({
        "unit_id": ObjectId(unit_id),
        "status": BookingStatus.pending,
        "$or": [
            {
                "$and": [
                    {"check_in_date": {"$lte": check_in_date}},
                    {"check_out_date": {"$gte": check_in_date}}
                ]
            },
            {
                "$and": [
                    {"check_in_date": {"$lte": check_out_date}},
                    {"check_out_date": {"$gte": check_out_date}}
                ]
            }
        ]
    }, {"$set": {"status": BookingStatus.cancelled}})


def update_booking_status(owner_id, booking_id, status):
    # update booking status
    booking = get_booking_by_id(booking_id)
    if booking is None:
        raise Exception("Booking not found")
    booking.status = status
    unit = get_unit_by_id(booking.unit_id)
    if unit is None:
        raise Exception("Unit in booking not found")
    if owner_id != unit.owner_id:
        raise Exception("Owner not authorized to update booking")
    MongoDB.booking.update_one({"_id": ObjectId(booking.id)}, {
                               "$set": booking.dict()})

    if status == BookingStatus.confirmed:
        # check if unit is available
        # check if dates do not overlap with "blocked_list" or "booked_list"
        check_blocked_dates(unit, booking.check_in_date,
                            booking.check_out_date)
        # check if dates do not overlap with "booked_list"
        check_booking_overlap(unit, booking.check_in_date,
                              booking.check_out_date)
        # clear all pending bookings in the same time frame
        clear_pending_bookings(
            booking.unit_id, booking.check_in_date, booking.check_out_date)

        #! add booking to unit only when it is (approved)/confirmed by owner
        unit.booked_list.append(BookingInUnit(
            **booking.dict(), _id=booking.id))
        MongoDB.units.update_one({"_id": ObjectId(unit.id)}, {
            "$set": unit.dict()})
        # ? cancel all other pending bookings in the same time frame
    # if booking was confirmed then got cancelled it should be removed from unit bookings list
    if booking.status == BookingStatus.confirmed and status != BookingStatus.confirmed:
        # Construct the MongoDB query to remove the item by ID
        query = {
            # Match the document containing the "booked_list" array
            "_id": ObjectId(unit.id),
            "booked_list.id": booking.id  # Match the booking item within the array by ID
        }
        # Execute the update query to pull the item from the array
        MongoDB.units.update_one(
            query, {"$pull": {"booked_list": {"id": booking.id}}})

    return booking


def get_unit_bookings(unit_id: str, pagination: Optional[PaginationIn] = None, status_filter: Optional[BookingStatus] = None, filter_after: Optional[datetime] = None, filter_before: Optional[datetime] = None
                      ) -> PaginatedList[BookingInDB]:
    """Gets all bookings for a unit."""
    # check if unit exists
    unit = get_unit_by_id(unit_id)
    if unit is None:
        raise Exception("Unit not found")

    # build the complex query
    # look for bookings with unit_id and with status filter and start/ end within filter_after and filter_before
    query = {"unit_id": ObjectId(unit_id)}
    if status_filter is not None:
        query["status"] = status_filter
    if filter_after is not None:
        query["check_in_date"] = {"$gte": filter_after}
    if filter_before is not None:
        query["check_out_date"] = {"$lte": filter_before}
    bookings = MongoDB.booking.find(query)

    if pagination is None:
        bookings = MongoDB.booking.find(query)
        pagination = PaginationIn(page=1, limit=1000)
    else:

        bookings = MongoDB.booking.find(query).skip(
            (pagination.page-1)*pagination.limit).limit(pagination.limit)

    bookings = [BookingInDB(**db_to_dict(booking)) for booking in bookings]
    total = MongoDB.booking.count_documents(query)
    return PaginatedList[BookingInDB](data=bookings, pagination=PaginationOut(page=pagination.page, num_items=pagination.limit, total=total))


def get_customer_bookings(customer_id, pagination):
    # check if customer exists
    customer = get_customer_by_id(customer_id)
    if customer is None:
        raise Exception("Customer not found")

    bookings = MongoDB.booking.find({"customer_id": ObjectId(customer_id)}).skip(
        (pagination.page-1)*pagination.limit).limit(pagination.limit)

    bookings = [BookingInDB(**db_to_dict(booking)) for booking in bookings]
    total = MongoDB.booking.count_documents(
        {"customer_id": ObjectId(customer_id)})
    return PaginatedList[BookingInDB](data=bookings, pagination=PaginationOut(page=pagination.page, num_items=pagination.limit, total=total))


def get_owner_bookings(owner_id: str, pagination: Optional[PaginationIn], status_filter: Optional[BookingStatus] = None, filter_after: Optional[datetime] = None, filter_before: Optional[datetime] = None
                       ) -> PaginatedList[BookingInDB]:
    # check if owner exists
    owner = get_owner_by_id(owner_id)
    if owner is None:
        raise Exception("Owner not found")

    # build the complex query
    # look for bookings with unit_id and with status filter and start/ end within filter_after and filter_before
    query = {"owner_id": owner_id}
    if status_filter is not None:
        query["status"] = status_filter
    if filter_after is not None:
        query["check_in_date"] = {"$gte": filter_after}
    if filter_before is not None:
        query["check_out_date"] = {"$lte": filter_before}
    bookings = MongoDB.booking.find(query)

    if pagination is None:
        bookings = MongoDB.booking.find(query)
        pagination = PaginationIn(page=1, limit=1000)

    else:
        bookings = MongoDB.booking.find(query).skip(
            (pagination.page-1)*pagination.limit).limit(pagination.limit)

    bookings = [BookingInDB(**db_to_dict(booking)) for booking in bookings]
    total = MongoDB.booking.count_documents(query)
    return PaginatedList[BookingInDB](data=bookings, pagination=PaginationOut(page=pagination.page, num_items=pagination.limit, total=total))
