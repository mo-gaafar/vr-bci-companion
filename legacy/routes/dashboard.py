from models.users import UserOut, RoleEnum
from util.security import verify_token_header, access_check
from models.users import RoleEnum
from util.security import access_check
from util.security import verify_token_header
from models.users import UserOut, UserIn, UserInDB
from models.common import CheckInHistory
from fastapi import APIRouter, Query, Depends, HTTPException, Header
from typing import Annotated, Optional, List
from util.multitenant import get_tenant_db
from util.parsing import guest_status_message
from util.scan_logs import get_scanlogs_sorted
from models.common import Histogram
from models.tickets import TicketsSummaryStatus, GuestInList, Ticket
from datetime import datetime
import numpy as np

dashboard = APIRouter(tags=["dashboard"])


# Core Dashboard

@dashboard.get("/status/tickets", response_model=TicketsSummaryStatus)
async def get_tickets_status(start_date: datetime, end_date: datetime, auth_user: UserOut = Depends(verify_token_header), tenant_id: str = Header(...)):
    access_check(auth_user, tenant_id, [RoleEnum.admin, RoleEnum.manager])
    # get tenant db
    db = get_tenant_db(tenant_id, precheck=True)
    # FIXME filter by venue id
    # find if date_start is in range or check_in is in range (to save memory and time) also is_valid is true
    tickets_find = db.tickets.find(
        {'$or': [{'date_start': {'$gte': start_date, '$lte': end_date}}, {'check_in': {'$gte': start_date, '$lte': end_date}},
                 {'date_expire': {'$gte': start_date, '$lte': end_date}},
                 {'check_out': {'$gte': start_date, '$lte': end_date}},
                 {'date_created': {'$gte': start_date, '$lte': end_date}}], 'is_valid': True})
    if tickets_find is None:
        raise HTTPException(status_code=404, detail="No tickets found")

    # convert objectid to str
    tickets = []
    for ticket in tickets_find:
        ticket["_id"] = str(ticket["_id"])
        # fix offset aware datetime
        ticket["date_start"] = ticket["date_start"].replace(tzinfo=None)
        ticket["date_created"] = ticket["date_created"].replace(tzinfo=None)
        if ticket["check_in"] is not None:
            ticket["check_in"] = ticket["check_in"].replace(tzinfo=None)
        if ticket["check_out"] is not None:
            ticket["check_out"] = ticket["check_out"].replace(tzinfo=None)
        if ticket["date_expire"] is not None:
            ticket["date_expire"] = ticket["date_expire"].replace(tzinfo=None)
        else:
            ticket["date_expire"] = ticket["date_start"]

        tickets.append(Ticket(**ticket))
    # fix offset aware datetime
    start_date = start_date.replace(tzinfo=None)
    end_date = end_date.replace(tzinfo=None)
    # print(tickets)

    # get number of tickets scanned in date range from check_in
    tickets_scanned_filt = []
    for ticket in tickets:
        if ticket.check_in is not None and ticket.is_active and ticket.check_in <= ticket.date_expire and ((ticket.date_start >= start_date and ticket.date_start <= end_date) or (ticket.date_expire >= start_date and ticket.date_expire <= end_date)):
            tickets_scanned_filt.append(ticket)
    num_tickets_scanned = len(tickets_scanned_filt)

    # get number of people who showed up
    tickets_showup_filt = []
    for ticket in tickets:
        if ticket.check_in is not None and ticket.check_out is not None and ((ticket.check_in >= start_date and ticket.check_in <= end_date) or (ticket.check_out >= start_date and ticket.check_out <= end_date)):
            tickets_showup_filt.append(ticket)
    num_people_showed_up = len(tickets_showup_filt)

    # get number of people who are in the venue
    num_people_in_venue = 0
    for ticket in tickets:
        
        if ticket.check_in is not None and ticket.is_active and ticket.check_in >= start_date and ticket.check_in <= end_date:
            num_people_in_venue += 1

    # total sold revenue
    total_bought_for_today = 0
    total_bought_revenue_for_today = 0
    total_bought_today = 0
    total_bought_revenue_today = 0
    for ticket in tickets:
        if (ticket.date_start >= start_date and ticket.date_start <= end_date) or (ticket.date_expire >= start_date and ticket.date_expire <= end_date):
            total_bought_revenue_for_today += ticket.price
            total_bought_for_today += 1
        if ticket.date_created >= start_date and ticket.date_created <= end_date:
            total_bought_revenue_today += ticket.price
            total_bought_today += 1

    return TicketsSummaryStatus(
        checked_in=num_tickets_scanned,
        total_left=num_people_showed_up,
        total_inside=num_people_in_venue,
        checked_out=num_tickets_scanned - num_people_in_venue,
        total_bought_for_today=total_bought_for_today,
        total_bought_revenue_for_today=total_bought_revenue_for_today,
        total_bought_today=total_bought_today,
        total_bought_revenue_today=total_bought_revenue_today

    )


@dashboard.get("/checkin/histogram", response_model=list[Histogram])
async def get_checkin_histogram(bin_minutes: int, start_date: datetime, end_date: datetime, tenant_id: str = Header(...), auth_user: UserOut = Depends(verify_token_header)):
    access_check(auth_user, tenant_id, [RoleEnum.admin, RoleEnum.manager])
    # get all checkin times from tickets collection in tenant db
    # get tenant db
    db = get_tenant_db(tenant_id, precheck=True)
    # get all checkin times
    # checkin_times = db.tickets.find(
    #     {'check_in': {'$gte': start_date, '$lte': end_date}})
    checkin_times = db.tickets.find(
        {'check_history': {'$elemMatch': {'is_checkin': True, 'timestamp': {'$gte': start_date, '$lte': end_date}}}})

    start_date = start_date.replace(tzinfo=None)
    end_date = end_date.replace(tzinfo=None)
    # create histogram with bins of width bin_minutes
    if end_date < start_date:
        raise HTTPException(
            status_code=400, detail="end_date must be greater than start_date")
    if (end_date - start_date).total_seconds() < bin_minutes:
        raise HTTPException(
            status_code=400, detail="bin_minutes must be less than date range")

    num_bins = int((end_date - start_date).total_seconds() //
                   (bin_minutes * 60))

    # checkin_times_arr = []
    # for checkin_time in checkin_times:
    #     checkin_times_arr.append(checkin_time['check_in'])

    checkin_times_arr = []
    for ticket in checkin_times:
        if len(ticket['check_history']) > 0:
            for check in ticket['check_history']:
                check = CheckInHistory(**check)
                if check.is_checkin and check.timestamp >= start_date and check.timestamp <= end_date:
                    checkin_times_arr.append(check.timestamp)

    histogram = [0] * num_bins
    for checkin_time in checkin_times_arr:
        hours = checkin_time.hour
        minutes = checkin_time.minute
        # convert to offsetnaive datetime
        checkin_time = checkin_time.replace(tzinfo=start_date.tzinfo)
        # get the bin for this checkin time, consider shifting to start time
        bin = int((checkin_time - start_date).total_seconds() //
                  (bin_minutes * 60))
        if bin >= num_bins:
            continue
        # print(bin)

        # add to histogram
        histogram[bin] += 1

    # convert to array of Histogram objects
    histogram_objects = []
    for i in range(len(histogram)):
        histogram_objects.append(
            Histogram(bin=i*bin_minutes, count=histogram[i]))

    return histogram_objects


@dashboard.get("/scan/recent", response_model=list[GuestInList])
async def get_recent_scans(start_date: datetime = Query(...), end_date: datetime = Query(...),
                           n_last: int = Query(...), venue_id: Optional[str] = Query(None),
                           tenant_id: str = Header(...), auth_user: UserOut = Depends(verify_token_header)):
    access_check(auth_user, tenant_id, [
                 RoleEnum.admin, RoleEnum.manager, RoleEnum.gatekeeper])
    # get tenant db
    db = get_tenant_db(tenant_id, precheck=True)

    # get all tickets scanned in date range (checkin or checkout) sorted by most recent
    # tickets_scanned = db.tickets.find(
    #     {'$or': [{'check_in': {'$gte': start_date, '$lte': end_date}},
    #              {'check_out': {'$gte': start_date, '$lte': end_date}}]})
    tickets_scanned = db.tickets.find(
        {'check_history': {'$elemMatch': {'timestamp': {'$gte': start_date, '$lte': end_date}}}})

    start_date = start_date.replace(tzinfo=None)
    end_date = end_date.replace(tzinfo=None)
    # convert objectid to str
    tickets = []
    for ticket in tickets_scanned:
        ticket["_id"] = str(ticket["_id"])
        tickets.append(Ticket(**ticket))

    scanlogs_sorted = get_scanlogs_sorted(tickets, n_last)

    # filter scanlogs by date range
    scanlogs_sorted_filt = []
    for scanlog in scanlogs_sorted:
        if scanlog.last_check >= start_date and scanlog.last_check <= end_date:
            scanlogs_sorted_filt.append(scanlog)

    # get all guests in venue
    return scanlogs_sorted_filt
