from models.notifications import OwnerNotification, OwnerNotificationType, BookingOutNotification, ApprovalOutNotification
from models.booking import BookingOutPublic, UnitBookingType
from models.common import PaginatedList, PaginationIn, PaginationOut
from models.units import UnitOutPublic, UnitLocation, UnitPricing
from models.units import LocationItem, LocationLevel
from datetime import datetime
from typing import Optional
from models.units import UnitOutPublic, UnitLocation, UnitPricing, ApprovalType, ApprovalStatus
from models.units import LocationItem, LocationLevel
from models.booking import BookingOutPublic, UnitBookingType, BookingStatus


def sort_notifications(notifications: list[OwnerNotification]) -> list[OwnerNotification]:
    return sorted(notifications, key=lambda x: x.timestamp, reverse=True)


def get_owner_notification_queue(pagination_in: PaginationIn, owner_id: str) -> PaginatedList[OwnerNotification]:
    """Gets a list of notifications for an owner."""
    # get the owner's unapproved units
    from repo.units import get_all_owner_units
    from repo.units import unitoutadmin_to_unitoutpublic
    units = get_all_owner_units(
        owner_id=owner_id, pagination=None).data

    notif_out = []
    # get approval notification and set timestamp to last_updates
    for unit in units:
        for approval in unit.approval_logs:
            # get last creation approval or rejection in the last 7 days
            if approval.approval_type == ApprovalType.creation and (datetime.utcnow() - approval.time_updated).days <= 7:
                if approval.approval_status == ApprovalStatus.approved:
                    new_notif = OwnerNotification(
                        title="Unit Approval",
                        title_l1="قبول الوحدة",
                        message="Your unit has been approved.",
                        message_l1="تم قبول وحدتك.",
                        read=False,
                        type=OwnerNotificationType.approval,
                        owner_id=owner_id,
                        approval_out=ApprovalOutNotification(
                            admin_comment=approval.admin_review,
                            unit_out=unitoutadmin_to_unitoutpublic(unit),
                        ),
                        timestamp=approval.time_updated,
                    )
                    notif_out.append(new_notif)
                elif approval.approval_status == ApprovalStatus.rejected:
                    new_notif = OwnerNotification(
                        title="Unit Rejection",
                        title_l1="رفض الوحدة",
                        message="Your unit has been rejected.",
                        message_l1="تم رفض وحدتك.",
                        read=False,
                        type=OwnerNotificationType.approval,
                        owner_id=owner_id,
                        approval_out=ApprovalOutNotification(
                            admin_comment=approval.admin_review,
                            unit_out=unitoutadmin_to_unitoutpublic(unit),
                        ),
                        timestamp=approval.time_updated,
                    )
                    notif_out.append(new_notif)

    # get the owner's unapproved bookings
    from repo.booking import get_owner_bookings
    bookings = get_owner_bookings(
        owner_id=owner_id, pagination=None, status_filter=BookingStatus.pending).data
    from repo.units import get_units_by_ids
    units = get_units_by_ids([booking.unit_id for booking in bookings])
    from repo.customer import get_customers_by_ids
    customers = get_customers_by_ids(
        [booking.customer_id for booking in bookings])
    # generate notifications for each
    for booking in bookings:
        for unit in units:
            # skip if unit is not active
            if unit.is_active == False:
                continue
            # check if booking belongs to unit and the check in is in the future
            if booking.unit_id == unit.id and booking.check_in_date > datetime.utcnow() :
                for customer in customers:
                    if booking.customer_id == customer.id:
                        new_notif = OwnerNotification(
                            title="Booking Request",
                            title_l1="طلب الحجز",
                            message="You have a new booking request.",
                            message_l1="لديك طلب حجز جديد.",
                            read=False,
                            type=OwnerNotificationType.booking,
                            owner_id=owner_id,
                            booking_out=BookingOutNotification(
                                _id=booking.id,
                                start_date=booking.check_in_date,
                                end_date=booking.check_out_date,
                                unit_out=unitoutadmin_to_unitoutpublic(unit),
                                booking_type=booking.booking_type,
                                name=str(customer.first_name) +
                                " " + str(customer.last_name),
                                email=customer.email,
                                phone=customer.phone,
                            ),
                            timestamp=booking.booking_date,
                        )
                        notif_out.append(new_notif)

    # order the notifications by timestamp
    sorted_notifications = sort_notifications(notif_out)

    return PaginatedList(pagination=PaginationOut(page=0, num_items=1000, total=1000, total_pages=1), data=sorted_notifications)
