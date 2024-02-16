from models.tickets import Ticket, GuestInList
from models.common import CheckInHistory


def scanlogs_to_message(is_checkin, timestamp=None, checkin_time=None, checkout_time=None):
    """Return a message for a scanlog."""
    if is_checkin:
        if checkout_time is None or checkin_time == timestamp:
            return "Checked in"
        else:
            return "Checked in again"
    else:
        if checkout_time is None or checkout_time != timestamp:
            return "Checked out"
        else:
            return "Last check out"


def get_scanlogs_sorted(tickets: list[Ticket], n_last) -> list[GuestInList]:
    """Return a list of scanlogs sorted by events in check_history."""

    if tickets is None:
        return []

    # create a list of scanlogs
    scanlogs = []
    for ticket in tickets:
        if ticket.check_history is None:
            continue
        for scan in ticket.check_history:
            scanlogs.append(GuestInList(
                name=ticket.guest_details.name,
                ticket_id=ticket.id,
                status_message=scanlogs_to_message(
                    scan.is_checkin, timestamp=scan.timestamp, checkout_time=ticket.check_out, checkin_time=ticket.check_in),
                is_active=ticket.is_active,
                payment_method=ticket.payment_method,
                ticket_tier_name=ticket.tier_name,
                last_check=scan.timestamp,
            ).dict())

    # sort the list of scanlogs by timestamp

    # convert all datetimes to offset aware
    # checkin_time = checkin_time.replace(tzinfo=start_date.tzinfo)

    for scan in scanlogs:
        scan['last_check'] = scan['last_check'].replace(tzinfo=None)
    scanlogs_sorted = sorted(
        scanlogs, key=lambda scan: scan['last_check'], reverse=True)
    scanlogs_objects = []
    for scan in scanlogs_sorted:
        # scan['last_check'] = scan['last_check'].isoformat() + "Z"
        scan = GuestInList(**scan)
        scanlogs_objects.append(scan)

    return scanlogs_objects[:n_last]
