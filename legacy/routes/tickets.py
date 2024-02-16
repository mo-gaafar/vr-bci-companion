from datetime import timedelta
from repository.tickets import get_ticket_by_id
from fastapi.responses import HTMLResponse
from models.users import UserOut, RoleEnum
from fastapi import APIRouter, Query, Depends, HTTPException, Header
from util.security import verify_token_header, access_check
from typing import Optional
from models.tickets import GuestInList, GuestTicketDetails, Ticket, ScanOut
from util.multitenant import check_tenancy, get_tenant_db
from util.parsing import guest_status_message
from util.scan_logs import scanlogs_to_message
from bson.objectid import ObjectId
from config.config import pytz_timezone
from datetime import datetime
from util.time import utcnow_iso
from config.config import DEVELOPMENT

tickets = APIRouter(tags=["tickets"])


def check_payment_status(ticket):
    if DEVELOPMENT is False:
        from models.orders import PaymentStatus
        from repository.orders import get_order
        db = get_tenant_db(ticket["tenant_id"], precheck=True)
        order = get_order(db, ticket["order_id"])
        if order.payment_data.status != PaymentStatus.completed:
            raise HTTPException(status_code=400, detail="Order not completed")


@tickets.post('/{id}/scan/', tags=['tickets'])
async def ticket_checkin(id: str, tenant_id: str = Header(...), auth_user: UserOut = Depends(verify_token_header)):
    # TODO: add scanner id to scan log later
    # TODO: check ticket is valid, not expired
    access_check(auth_user, tenant_id, [
                 RoleEnum.admin, RoleEnum.manager, RoleEnum.gatekeeper])
    # get tenant db
    db = get_tenant_db(tenant_id, precheck=True)
    # check if ticket exists
    ticket = get_ticket_by_id(db, ticket_id=id)

    # check if ticket is paid
    if ticket.check_history is None:
        ticket.check_history = []

    if DEVELOPMENT is False:
        if ticket.is_valid is False:
            raise HTTPException(status_code=400, detail="Ticket not paid")
        if ticket.is_valid is None:
            raise HTTPException(status_code=400, detail="Ticket not paid")
        # check if ticket hasnt started yet
        # check if ticket has expired
        if ticket.date_start is None:
            raise HTTPException(
                status_code=400, detail="Ticket has no start date")
        if ticket.date_expire is None:
            # add 1 day to start date
            ticket.date_expire = ticket.date_start + \
                timedelta(days=1)
        if ticket.date_start > datetime.utcnow():
            raise HTTPException(
                status_code=400, detail="Ticket has not started yet")
        if ticket.date_expire < datetime.utcnow():
            if not ticket.is_active:
                raise HTTPException(
                    status_code=400, detail="Ticket has expired")

    if ticket.check_in is None:
        # check in
        is_checkin = True
        is_active = True
        updateset = {
            "is_active": is_active,
            "check_in": datetime.utcnow()
        }
    elif ticket.check_out is None:
        # check out
        is_checkin = False
        is_active = False
        updateset = {
            "is_active": is_active,
            "check_out": datetime.utcnow()
        }
    else:
        if ticket.is_active:
            # check out again
            is_checkin = False
            is_active = False
            updateset = {
                "is_active": is_active,
                "check_out": datetime.utcnow()
            }
        else:
            # check in again
            is_checkin = True
            is_active = True
            updateset = {
                "is_active": is_active,
            }

    db.tickets.update_one(
        {"_id": ObjectId(id)}, {
            "$set": updateset,
            "$push": {
                "check_history": {
                    "is_checkin": is_checkin,
                    "timestamp": datetime.utcnow()
                }}}, upsert=True)

    return ScanOut(guest_info=ticket.guest_details,
                   is_active=is_active,
                   tier_name=ticket.tier_name,
                   message=scanlogs_to_message(is_checkin, ticket.check_out))


@tickets.get("/guests/detailed", tags=["backend_admin"], response_model=GuestTicketDetails)
async def get_ticket_details(ticket_id: str = Query(...), tenant_id: str = Header(...), auth_user: UserOut = Depends(verify_token_header)):
    """Returns a list of all guests and their ticket details"""
    access_check(auth_user, tenant_id, [
        RoleEnum.admin, RoleEnum.manager, RoleEnum.gatekeeper])
    # get tenant db
    db = get_tenant_db(tenant_id, precheck=True)
    ticket = get_ticket_by_id(db, ticket_id)

    ticket_dict = ticket.dict()
    guest_details_dict = ticket.guest_details.dict()
    guest_details_dict.pop("id")
    ticket_dict.pop("guest_details")

    # get last check
    last_check = None
    if ticket.check_history:
        last_check = ticket.check_history[-1].timestamp

    # reverse check history array
    reverse = []
    if ticket.check_history is not None:
        reverse = ticket.check_history[::-1]

    ticket_dict["check_history"] = reverse

    guest_ticket_details = GuestTicketDetails(ticket_id=ticket.id,
                                              ticket_tier_name=ticket.tier_name,
                                              **guest_details_dict,
                                              **ticket_dict,
                                              status_message=guest_status_message(
                                                  ticket),
                                              last_check=last_check
                                              )
    return guest_ticket_details


@tickets.get("/guests/all", tags=["backend_admin"], response_model=list[GuestInList])
async def get_guest_list(tenant_id: str = Header(...), auth_user: UserOut = Depends(verify_token_header), start_date: Optional[datetime] = Query(None), end_date: Optional[datetime] = Query(None), venue_id: Optional[str] = Query(None)):
    """Returns a list of all guests and their ticket details""
    """
    # [x] add date range filter
    # [x] find all tickets
    # [x] reformat to GuestInList
    # [x] create cute status message based on guest activity

    # TODO: add venue filter

    access_check(auth_user, tenant_id, [
        RoleEnum.admin, RoleEnum.manager])

    db = get_tenant_db(tenant_id, precheck=True)

    if None not in [end_date, start_date]:
        find = db.tickets.find(
            {'is_valid': True,
             '$or': [{'check_in': {'$gte': start_date, '$lte': end_date}},
                     {'check_out': {
                         '$gte': start_date, '$lte': end_date}},
                     {'date_start': {
                         '$gte': start_date, '$lte': end_date}},
                     {'date_expire': {
                         '$gte': start_date, '$lte': end_date}}
                     #  {'date_created':{'gte':start_date, '$lte': end_date}}
                     ]})
    else:
        find = db.tickets.find()
    if find is None:
        raise HTTPException(status_code=404, detail="No tickets found")

    # convert results to array of dicts

    tickets = []
    for ticket in find:
        ticket["_id"] = str(ticket["_id"])
        tickets.append(ticket)

    ticket_objects = [Ticket(**ticket) for ticket in tickets]

    guest_ticket_summaries = []
    for ticket in ticket_objects:
        # print(ticket.is_active)
        last_check = None
        if ticket.is_active:
            last_check = ticket.check_in
        else:
            last_check = ticket.check_out

        guest_ticket_summary = GuestInList(
            name=ticket.guest_details.name,
            ticket_id=ticket.id,
            ticket_tier_name=ticket.tier_name,
            status_message=guest_status_message(ticket),
            is_active=ticket.is_active,
            payment_method=ticket.payment_method,
            last_check=last_check,
        )
        guest_ticket_summaries.append(guest_ticket_summary)

    return guest_ticket_summaries


@tickets.get("/{tenant_id}/{ticket_id}/iframe", response_class=HTMLResponse)
async def get_ticket_iframe(ticket_id: str, tenant_id: str):
    from util.ticket_render import get_ticket_html
    from models.business import Venue
    from repository.orders import get_order
    from repository.business import get_venue
    import os
    db = get_tenant_db(tenant_id, precheck=True)
    ticket = get_ticket_by_id(db, ticket_id)
    order = get_order(db, ticket.order_id)
    venue = get_venue(db, ticket.venue_id)
    parent_dir = os.path.dirname(os.path.dirname(__file__))
    html = get_ticket_html(ticket_id=ticket_id, order=order, venue=venue,
                           html_content=parent_dir+'/templates/ticket.html', css_content=parent_dir+'/templates/style.css', is_filepath=True)
    return html
