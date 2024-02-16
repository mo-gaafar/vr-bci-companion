from fastapi import Depends
from util.security import verify_token_header, access_check
from models.users import UserOut
from models.common import CustomerRetention
from models.common import TicketTierSummary
from models.common import PaymentMethodSummary
from models.tickets import Ticket
from models.common import AnalyticSummary, SalesHistogram
from models.orders import Order
from models.common import Histogram
from fastapi import HTTPException
from datetime import timedelta
from fastapi import APIRouter, Query, Header, HTTPException
from typing import Optional
from util.multitenant import check_tenancy, get_tenant_db
from bson.objectid import ObjectId
from datetime import datetime

analytics = APIRouter(tags=["analytics"])


# Customers


@analytics.get("/customers/retention/tickettier", response_model=list[CustomerRetention])
async def get_customer_retention_by_tickettier(include_absent: bool = Query(...), venue_id: Optional[str] = Query(None), start_date: datetime = Query(datetime(1970, 1, 1)), end_date: datetime = Query(datetime.utcnow()), auth_user: UserOut = Depends(verify_token_header), tenant_id: str = Header(...)):
    """Returns the customer retention rate by ticket tier for a given date range."""
    db = get_tenant_db(tenant_id, precheck=True)
    # TODO: add venue id filter
    query = db.tickets.find({"date_start": {
                            "$gte": start_date, "$lte": end_date}, "is_valid": True})
    query = list(query)
    query_filtered = []
    for ticket in query:
        ticket["_id"] = str(ticket["_id"])
        ticket = Ticket(**ticket)
        if include_absent is True:
            query_filtered.append(ticket)
        else:
            if ticket.check_in is not None and ticket.check_out is not None:
                query_filtered.append(ticket)

    time_mins_by_tier = {}
    total_count_by_tier = {}
    for ticket in query_filtered:
        if ticket.tier_name not in time_mins_by_tier:
            time_mins_by_tier[ticket.tier_name] = 0
            total_count_by_tier[ticket.tier_name] = 0
        time_mins_by_tier[ticket.tier_name] += calculate_time_stay_from_ticket(
            ticket)
        total_count_by_tier[ticket.tier_name] += 1

    tier_summaries = []
    for tier_name in time_mins_by_tier:
        total_customers = total_count_by_tier[tier_name]
        total_mins_stayed = time_mins_by_tier[tier_name]
        avg_mins_stayed = time_mins_by_tier[tier_name] / \
            total_customers if total_customers != 0 else 0
        tier_summaries.append(CustomerRetention(
            tier_name=tier_name, total_customers=total_customers,
            total_mins_stayed=total_mins_stayed, avg_mins_stayed=avg_mins_stayed))

    # overall
    total_customers = sum(total_count_by_tier.values())
    total_mins_stayed = sum(time_mins_by_tier.values())
    avg_mins_stayed = total_mins_stayed / \
        total_customers if total_customers != 0 else 0
    tier_summaries.append(CustomerRetention(total_customers=total_customers,
                                            tier_name="Total", total_mins_stayed=total_mins_stayed, avg_mins_stayed=avg_mins_stayed))

    return tier_summaries


def calculate_time_stay_from_ticket(ticket: Ticket):
    if ticket.check_history is None:
        if ticket.check_in is None or ticket.check_out is None:
            return 0
        return (ticket.check_out - ticket.check_in).total_seconds() // 60

    # calculate from checkin and checkout timestamps in checkin history
    total_time_min = 0
    for check in ticket.check_history:
        if check.is_checkin is True:
            check_in = check.timestamp
        else:
            check_out = check.timestamp
            total_time_min += (check_out - check_in).total_seconds() // 60
    return total_time_min

# Financials


@analytics.get("/financials/sales/orders/histogram", response_model=list[SalesHistogram])
async def get_sales_histogram(bin_minutes: int = Query(...), venue_id: Optional[str] = Query(None), start_date: datetime = Query(datetime(1970, 1, 1)), end_date: datetime = Query(datetime.utcnow()), auth_user: UserOut = Depends(verify_token_header), tenant_id: str = Header(...)):
    """Returns a histogram of order sales by bin_minutes (in minutes) for a given date range."""
    # TODO: add venue_id filter
    if end_date < start_date:
        raise HTTPException(
            status_code=400, detail="end_date must be greater than start_date")
    if (end_date - start_date).total_seconds() < bin_minutes:
        raise HTTPException(
            status_code=400, detail="bin_minutes must be less than date range")

    db = get_tenant_db(tenant_id, precheck=True)
    query = db.orders.find({"payment_data.date_completed": {
                           "$gte": start_date, "$lte": end_date}})

    num_bins = int((end_date - start_date).total_seconds() //
                   (bin_minutes * 60))

    filter_items_arr = []
    for order in query:
        filter_items_arr.append(
            {'date_completed': order['payment_data']['date_completed'], 'total': order['payment_data']['total_amount']})

    histogram = [0] * num_bins
    histogram_sum = [0] * num_bins
    for item in filter_items_arr:
        date_completed = item['date_completed']
        date_completed = date_completed.replace(tzinfo=start_date.tzinfo)
        hours = date_completed.hour
        minutes = date_completed.minute
        bin = int((date_completed - start_date).total_seconds() //
                  (bin_minutes * 60))
        if bin >= num_bins:
            continue
        histogram[bin] += 1
        histogram_sum[bin] += item['total']

    histogram_objects = []
    for i in range(len(histogram)):
        histogram_objects.append(
            SalesHistogram(bin=i * bin_minutes, count=histogram[i], total_amount=histogram_sum[i]))

    return histogram_objects


@analytics.get("/financials/sales/orders", response_model=AnalyticSummary)
async def get_total_sales(venue_id: Optional[str] = Query(None), start_date: datetime = Query(datetime(1970, 1, 1)), end_date: datetime = Query(datetime.utcnow()), auth_user: UserOut = Depends(verify_token_header), tenant_id: str = Header(...)):
    # TODO add venue_id filter
    db = get_tenant_db(tenant_id, precheck=True)
    query = db.orders.find({"payment_data.date_completed": {
                            "$gte": start_date, "$lte": end_date}})
    order_arr = []
    sum_total = 0
    sum_count = 0
    avg_total = 0
    for order in query:
        order["_id"] = str(order["_id"])
        order_obj = Order(**order)
        sum_total += order_obj.payment_data.total_amount
        sum_count += 1
    if sum_count != 0:
        avg_total = sum_total / sum_count
    return AnalyticSummary(total=sum_total, count=sum_count, average=avg_total)


@analytics.get("/financials/sales/tickets/histogram", response_model=list[SalesHistogram])
async def get_ticket_sales_histogram(bin_minutes: int = Query(...), venue_id: Optional[str] = Query(None), start_date: datetime = Query(datetime(1970, 1, 1)), end_date: datetime = Query(datetime.utcnow()), auth_user: UserOut = Depends(verify_token_header), tenant_id: str = Header(...)):
    """Returns a histogram of ticket sales by bin_minutes (in minutes) for a given date range."""
    db = get_tenant_db(tenant_id, precheck=True)
    query = db.tickets.find({"date_created": {
                            "$gte": start_date, "$lte": end_date}, "is_valid": True})
    num_bins = int((end_date - start_date).total_seconds() //
                   (bin_minutes * 60))

    filter_items_arr = []
    for ticket in query:
        filter_items_arr.append(
            {'date_created': ticket['date_created'], 'total': ticket['price']})

    histogram = [0] * num_bins
    histogram_sum = [0] * num_bins
    for item in filter_items_arr:
        date_created = item['date_created']
        date_created = date_created.replace(tzinfo=start_date.tzinfo)
        hours = date_created.hour
        minutes = date_created.minute
        bin = int((date_created - start_date).total_seconds() //
                  (bin_minutes * 60))
        if bin >= num_bins:
            continue
        histogram[bin] += 1
        histogram_sum[bin] += item['total']

    histogram_objects = []
    for i in range(len(histogram)):
        histogram_objects.append(
            SalesHistogram(bin=i * bin_minutes, count=histogram[i], total_amount=histogram_sum[i]))
    print(histogram_objects)
    return histogram_objects


@analytics.get("/financials/sales/tickets", response_model=AnalyticSummary)
async def get_total_ticket_sales(venue_id: Optional[str] = Query(None), start_date: datetime = Query(datetime(1970, 1, 1)), end_date: datetime = Query(datetime.utcnow()), auth_user: UserOut = Depends(verify_token_header), tenant_id: str = Header(...)):
    db = get_tenant_db(tenant_id, precheck=True)
    query = db.tickets.find({"date_created": {
                            "$gte": start_date, "$lte": end_date}, "is_valid": True})
    sum_total = 0
    sum_count = 0
    avg_total = 0
    for ticket in query:
        sum_total += ticket['price']
        sum_count += 1
    if sum_count != 0:
        avg_total = sum_total / sum_count

    return AnalyticSummary(total=sum_total, count=sum_count, average=avg_total)


@analytics.get("/financials/payment-methods", response_model=list[PaymentMethodSummary])
async def get_payment_method_summary(venue_id: Optional[str] = Query(None), start_date: datetime = Query(datetime(1970, 1, 1)), end_date: datetime = Query(datetime.utcnow()), auth_user: UserOut = Depends(verify_token_header), tenant_id: str = Header(...)):
    db = get_tenant_db(tenant_id, precheck=True)
    query = db.orders.find({"payment_data.date_completed": {
                            "$gte": start_date, "$lte": end_date}})
    sum_total = 0
    sum_count = 0
    avg_total = 0
    payment_method_dict = {}
    payment_method_dict_amount = {}
    for order in query:
        order["_id"] = str(order["_id"])
        order_obj = Order(**order)
        payment_method = order_obj.payment_data.method
        if payment_method not in payment_method_dict:
            payment_method_dict[payment_method] = 0
            payment_method_dict_amount[payment_method] = 0
        payment_method_dict[payment_method] += 1
        payment_method_dict_amount[payment_method] += order_obj.payment_data.total_amount
        sum_total += order_obj.payment_data.total_amount
        sum_count += 1
    percentage_dict_count = {}
    percentage_dict_total = {}
    for key in payment_method_dict:
        percentage_dict_count[key] = payment_method_dict[key] / sum_count
        percentage_dict_total[key] = payment_method_dict_amount[key] / sum_total

    payment_method_summary_arr = []
    for key in percentage_dict_count:
        payment_method_summary_arr.append(
            PaymentMethodSummary(method_name=key, total=payment_method_dict[key], percentage_from_order_count=percentage_dict_count[key], percentage_from_total=percentage_dict_total[key]))

    return payment_method_summary_arr


@analytics.get("/financials/sales/tiers", response_model=list[TicketTierSummary])
async def get_ticket_tier_summary(venue_id: Optional[str] = Query(None), start_date: datetime = Query(datetime(1970, 1, 1)), end_date: datetime = Query(datetime.utcnow()), auth_user: UserOut = Depends(verify_token_header), tenant_id: str = Header(...)):
    """Returns a list of ticket tier summaries for a given date range. 
    the summary includes th2e name of the ticket tier, the number of tickets sold, the total amount of tickets sold,
    the percentage of tickets sold, both by count and by total amount."""
    # TODO: add venue_id filtering
    db = get_tenant_db(tenant_id, precheck=True)
    query = db.tickets.find({"date_created": {
                            "$gte": start_date, "$lte": end_date}, "is_valid": True})
    # print(list(query))
    ticket_tier_dict = {}
    ticket_tier_dict_amount = {}
    sum_total = 0
    sum_count = 0
    for ticket in query:
        ticket["_id"] = str(ticket["_id"])
        ticket_obj = Ticket(**ticket)
        ticket_tier = ticket_obj.tier_name
        # print(ticket_tier)
        if ticket_tier not in ticket_tier_dict:
            ticket_tier_dict[ticket_tier] = 0
            ticket_tier_dict_amount[ticket_tier] = 0
        ticket_tier_dict[ticket_tier] += 1
        ticket_tier_dict_amount[ticket_tier] += ticket_obj.price
        sum_total += ticket_obj.price
        sum_count += 1
    percentage_dict_count = {}
    percentage_dict_total = {}
    for key in ticket_tier_dict:
        percentage_dict_count[key] = ticket_tier_dict[key] / sum_count
        percentage_dict_total[key] = ticket_tier_dict_amount[key] / sum_total

    ticket_tier_summary_arr = []
    for key in percentage_dict_count:
        ticket_tier_summary_arr.append(
            TicketTierSummary(tier_name=key, total_price=ticket_tier_dict_amount[key], total_count=ticket_tier_dict[key],
                              percentage_from_ticket_count=percentage_dict_count[key], percentage_from_revenue=percentage_dict_total[key]))

    return ticket_tier_summary_arr
