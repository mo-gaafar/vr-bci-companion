from repository.tickets import get_ticket_by_id, get_tickets_in_order
from repository.business import get_venue, get_business
from repository.orders import delete_order
from repository.orders import get_order
from models.tickets import TicketDisplay
from models.orders import OrderOut
from util.brevo import brevo_send_message_file
from util.ticketgen import format_order_invitation, format_ticket_invitation, generate_ticket_order_pdf, generate_qr_code_png
import hashlib
import hmac
import os
from fastapi import FastAPI, Query
from util.parsing import create_ticket_dict
from fastapi import APIRouter, Header, HTTPException, Form, UploadFile, File, Depends, Query, BackgroundTasks, Body, Request
from fastapi.responses import StreamingResponse, RedirectResponse
from typing import Annotated, Optional
from repository.db import admin_db
from models.orders import Order, OrderCheckoutIn, TicketTier, OrderItem, OrderCheckoutOut, OrderPayment, PaymentMethod, PaymentStatus
from models.customer import OrderCustomer, Customer
from models.business import Business, Venue
from models.tickets import Ticket
from util.multitenant import check_tenancy, get_tenant_db
from bson.objectid import ObjectId

orders = APIRouter(tags=["orders"])


def check_customer_exist(email, phone, tenant_id):
    ''' Consolidate customers with same phone or email
    return customer_id if customer exists
    '''
    # [ ] update customer if given one of email or phone and fix it
    # check if customer exists from phone or email
    if email is not None or phone is not None:
        tenant_db = get_tenant_db(tenant_id)
        # find customer with same email or phone
        customer = tenant_db.customers.find_one(
            {"email": email, "phone": phone})
        if customer is not None:
            return customer['_id']
        # else:
        #     # find customer with same email
        #     customer = tenant_db.customers.find_one({"email": email})
        #     # overwrite phone number

        #     if customer is not None:
        #         return customer['_id']

    if email is None and phone is None:
        raise HTTPException(
            status_code=400, detail="Email or phone must be provided")
    print("Customer does not exist")
    return None


def create_customer(customer, tenant_id) -> OrderCustomer:
    ''' Create customer if customer does not exist'''

    # check if customer exists from phone or email
    customer_id = check_customer_exist(
        customer.email, customer.phone, tenant_id)

    tenant_db = get_tenant_db(tenant_id)

    if customer_id is None:
        # create customer
        customer = Customer(**customer.dict(), order_ids=[], ticket_ids=[])
        customer_id = tenant_db.customers.insert_one(
            customer.dict()).inserted_id
        print("Created customer" + str(customer_id))
        return OrderCustomer(**customer.dict(), _id=str(customer_id))

    order_customer = OrderCustomer(**customer.dict(), _id=str(customer_id))
    return order_customer


def add_ticket_to_customer(order_customer: OrderCustomer, tenant_id, ticket_id=None, order_id=None):
    ''' Add ticket to customer '''
    tenant_db = get_tenant_db(tenant_id)
    # create customer if not exist
    customer = create_customer(order_customer, tenant_id)
    customer_id = customer.id
    # add ticket to customer
    # check if order_id is None
    if order_id is None:
        tenant_db.customers.update_one({"_id": ObjectId(customer_id)}, {
            "$push": {"ticket_ids": ticket_id}})
        return customer_id
    if ticket_id is None:
        tenant_db.customers.update_one({"_id": ObjectId(customer_id)}, {
            "$push": {"order_ids": order_id}})
        return customer_id
    else:
        tenant_db.customers.update_one({"_id": ObjectId(customer_id)}, {
            "$push": {"ticket_ids": ticket_id, "order_ids": order_id}})
        return customer_id


def finalize_order_tickets(order: Order, tenant_id) -> Order:
    ''' Finalize order and tickets and add to customer '''

    # [x] create ticket object for each order item
    # [x] add order_id to buyer
    # [x] add ticket_id to each orderitem and create ticket object
    # [x] add ticket_id to customer
    tenant_db = get_tenant_db(tenant_id)

    try:
        # get ticket tier details
        find_ticket_tiers = tenant_db.ticket_tiers.find(
            {"_id": {"$in": [ObjectId(item.ticket_tier_id) for item in order.order_items]}})

        ticket_tier_details = {}

        for ticket_tier in find_ticket_tiers:
            ticket_tier_dict = dict(ticket_tier)
            ticket_tier_id = str(ticket_tier_dict['_id'])
            ticket_tier_details[ticket_tier_id] = ticket_tier_dict

        # print("Tiers", ticket_tier_details)

        # create ticket object for each order item
        # add order_id to buyer
        order.buyer.id = add_ticket_to_customer(
            order.buyer, tenant_id, order_id=order.id)
        for item in order.order_items:
            print(item.dict())
            # creating ticket object and updating price
            price = ticket_tier_details[item.ticket_tier_id]['price']
            amenities = ticket_tier_details[item.ticket_tier_id]['amenities']
            item.ticket_tier_price = price
            ticket = Ticket(**item.dict(), order_id=order.id, venue_id=order.venue_id,  # type: ignore
                            tier_id=item.ticket_tier_id, tier_name=item.ticket_tier_name, price=price,
                            guest_details=item.customer, payment_method=order.payment_data.method,
                            amenities=amenities)

            # add ticket_id to each orderitem and create ticket object
            ticket_id = tenant_db.tickets.insert_one(ticket.dict()).inserted_id
            # add ticket_id to order_item
            item.ticket_id = str(ticket_id)
            # add ticket_id to customer
            item.customer.id = add_ticket_to_customer(
                item.customer, tenant_id, ticket_id=str(ticket_id))
            # add customer_id to ticket
            tenant_db.tickets.update_one({"_id": ObjectId(ticket_id)}, {
                "$set": {"guest_details": item.customer.dict()}})

        # update order.order_items with ticket_id for each item
        # update orderitems and buyer in order
        tenant_db.orders.update_one({"_id": ObjectId(order.id)}, {
            "$set": {"order_items": [item.dict() for item in order.order_items], "buyer": order.buyer.dict()}})

        return order

    except Exception as e:
        print(e)
        # rollback order on failure
        # [ ] delete order
        # [ ] delete tickets
        # [ ] delete tickets from customer

        # find order and delete
        tenant_db.orders.delete_one({"_id": ObjectId(order.id)})
        # find tickets and delete
        tenant_db.tickets.delete_many({"order_id": order.id})
        # find buyer and delete order_id
        tenant_db.customers.update_one({"_id": ObjectId(order.buyer.id)}, {
            "$pull": {"order_ids": order.id}})
        # find customer and delete ticket_ids
        ticket_ids = [ticket.ticket_id for ticket in order.order_items]
        tenant_db.customers.update_one({"_id": ObjectId(order.buyer.id)}, {
            "$pull": {"ticket_ids": {"$in": ticket_ids}}})

        raise HTTPException(
            status_code=400, detail="Error finalizing order, rolling back")


def validate_orderitems(order_items: list[OrderItem], tenant_id):
    ''' Validate order items and fill in missing information'''
    # [x] check if customer exists
    # [x] check if ticket tier exists
    # [x] check if ticket tier is sold out
    # [ ] check if ticket tier is expired
    # create array of ticket tiers from order_items

    # check if ticket tiers exist with same name and id
    tenant_db = get_tenant_db(tenant_id)
    all_ticket_tiers = list(tenant_db.ticket_tiers.find())
    # convert id to str
    for tier in all_ticket_tiers:
        tier['_id'] = str(tier['_id'])

    for item in order_items:
        # check if ticket tier exists with same name and id
        # find matching ticket tier
        ticket_tier = None
        tier_idx = 0
        for tier in all_ticket_tiers:
            if tier['name'] == item.ticket_tier_name and tier['_id'] == item.ticket_tier_id:
                ticket_tier = tier
                tier_idx = all_ticket_tiers.index(tier)
                break
            if tier['_id'] == item.ticket_tier_id and item.ticket_tier_name == None:
                ticket_tier = tier
                tier_idx = all_ticket_tiers.index(tier)
                break
            # if tier['name'] == item.ticket_tier_name and item.ticket_tier_id == None:
            #     ticket_tier = tier
            #     tier_idx = all_ticket_tiers.index(tier)
            #     break

        if ticket_tier is None:
            raise HTTPException(
                status_code=400, detail="Ticket tier does not exist")

        # check if ticket tier is sold out
        all_ticket_tiers[tier_idx]['quantity_sold'] -= 1
        if all_ticket_tiers[tier_idx]['max_quantity'] - all_ticket_tiers[tier_idx]['quantity_sold'] < 0:
            raise HTTPException(
                status_code=400, detail="Ticket tier is sold out")

        # check if ticket tier is expired
        # if ticket_tier['expiry_date'] < datetime.utcnow():

        # fix ticket tier name and id
        item.ticket_tier_name = ticket_tier['name']
        item.ticket_tier_id = ticket_tier['_id']
        order_items[order_items.index(item)] = item

        # check customer data integrity
        check_customer_exist(item.customer.email,
                             item.customer.phone, tenant_id)
    print("Validated order items")
    return order_items


def calculate_total_amount(order_items: list[OrderItem], tenant_id):
    ''' Calculate total amount of order '''
    db = get_tenant_db(tenant_id, precheck=True)
    # get ticket tier details
    find_ticket_tiers = db.ticket_tiers.find(
        {"_id": {"$in": [ObjectId(item.ticket_tier_id) for item in order_items]}})

    ticket_tier_details = {}

    for ticket_tier in find_ticket_tiers:
        ticket_tier_dict = dict(ticket_tier)
        ticket_tier_id = str(ticket_tier_dict['_id'])
        ticket_tier_details[ticket_tier_id] = ticket_tier_dict

    # print("Tiers", ticket_tier_details)
    total_amount = 0

    for item in order_items:
        # creating ticket object and updating price
        price = ticket_tier_details[item.ticket_tier_id]['price']
        item.ticket_tier_price = price
        total_amount += price

    return total_amount


def update_payment_status(order: Order, tenant_id, payment_status: PaymentStatus):
    # [ ] update payment status in order
    # [ ] update payment status in tickets
    pass


def find_duplicate_order(order: Order, tenant_id):
    # TODO: fix this to save performance
    if order.id is None:
        return

    db = get_tenant_db(tenant_id, precheck=True)
    # lookup order by order items and buyer
    # find_order = db.orders.find_one({"order_items": [item.dict(
    # ) for item in order.order_items], "buyer": order.buyer.dict()})
    # use $ match to find order with same order items and buyer exclude customer id and ticket_id and _id
    # find_order = db.orders.aggregate([
    #     {"$match": {"order_items": [item.dict(exclude={"ticket_id", "customer.id", "id"})
    #                                 for item in order.order_items], "buyer": order.buyer.dict(exclude={"id"})}},
    #     {"$project": {"_id": 1}}])

    # if find_order is None:
    #     return
    # else:
    #     find_order["_id"] = str(find_order["_id"])
    #     order = Order(**find_order)
    #     if order.payment_data.status == PaymentStatus.completed:
    #         return
    #     else:
    #         print("Found duplicate order")
    #         return OrderCheckoutOut(order_id=order.id, payment_url=f"/api/v1/payment/link/{tenant_id}/{order.id}", payment_method=order.payment_data.method, status=order.payment_data.status)


@orders.post("/checkout", response_model=OrderCheckoutOut)
async def checkout_order(background_tasks: BackgroundTasks, order_in: OrderCheckoutIn,
                         tenant_id: str = Header(...)):
    # get tenant db
    db = get_tenant_db(tenant_id, precheck=True)

    # check venue
    venue = get_venue(db, order_in.venue_id)
    # buyer customer
    buyer = order_in.buyer
    check_customer_exist(buyer.email, buyer.phone, tenant_id)

    order_in.order_items = validate_orderitems(
        order_in.order_items, tenant_id)

    if order_in.promocode == "FREEPROMO23":
        # look for ticket tier with name "Free"
        free_ticket_tier = None
        free_tier = db.ticket_tiers.find_one({"name": "Free"})
        if free_tier is None:
            raise HTTPException(
                status_code=400, detail="Free ticket tier not found")
        free_tier['_id'] = str(free_tier['_id'])
        free_ticket_tier = TicketTier(**free_tier)
        for item in order_in.order_items:
            item.ticket_tier_id = free_ticket_tier.id
            item.ticket_tier_name = free_ticket_tier.name
            item.ticket_tier_price = free_ticket_tier.price

    # check if order has been ordered before and is not paid by checking if same order items exist and is not paid
    # duplicate_order = find_duplicate_order(order_in, tenant_id)
    # if duplicate_order is not None:
    #     return duplicate_order
    # calculate total amount

    total_amount = calculate_total_amount(
        order_in.order_items, tenant_id)

    payment_data = OrderPayment(
        total_amount=total_amount, method=order_in.payment_method)  # type: ignore

    # create order in db
    new_order = Order(**order_in.dict(), payment_data=payment_data)
    order_id = db.orders.insert_one(new_order.dict()).inserted_id
    new_order.id = str(order_id)

    finalized_order = finalize_order_tickets(new_order, tenant_id)

    payment_url = None

    # using paymob v2, create order intentions
    # if payment method is cash, create order in db and return order id
    if order_in.payment_method == PaymentMethod.cash:
        payment_url = None
        # FIXME how to handle cash payments
        # type: ignore
        pass
    elif order_in.payment_method == PaymentMethod.card:
        # FIXME how to handle card payments

        from util.paymob_accept import initiate_payment

        business = get_business(tenant_id)
        api_key = business.payment_api_key
        integration_id = business.payment_integration_id
        frame_id = business.payment_frame_id

        payment_url, trx_id = initiate_payment(
            finalized_order, api_key, integration_id, frame_id)
        # update order with trx id
        db.orders.update_one({'_id': ObjectId(order_id)}, {
            '$set': {'payment_data.transaction_id': trx_id}})

    return OrderCheckoutOut(order_id=finalized_order.id, payment_url=payment_url, payment_method=order_in.payment_method, status=PaymentStatus.pending)
    # return RedirectResponse(payment_url , status_code=303)

    # if payment method is card, create order in db and return order id and payment url


async def invite_order_tickets_task(tenant_id, order_id, resend=False):
    '''
    Send invitation email to order buyer and guests
    '''
    # get venue
    db = get_tenant_db(tenant_id, precheck=True)
    rendered_html = True  # ! TODO: change this to false after testing

    # get business
    business = get_business(tenant_id)
    # get order
    order = get_order(db, order_id)
    # get venue
    venue = get_venue(db, order.venue_id)
    # get tickets
    ticket_objs = get_tickets_in_order(db, order_id)

    # try:
    if order.message_sent is False or resend is True:
        # send email to order buyer
        subject, msg_body = format_order_invitation(venue, business, order)
        # generate pdf
        from util.parsing import create_ticket_dict, prepare_ticket_render_dictlist
        if rendered_html is False:
            ticket_data_array = create_ticket_dict(order.id, order)
        else:
            ticket_data_array = prepare_ticket_render_dictlist(
                order, venue)
        pdf_path = "/tmp/ticket.pdf"

        await generate_ticket_order_pdf(
            ticket_data_array, filename=pdf_path, rendered_html=rendered_html)

        # send email
        if order.buyer.email is None:
            raise Exception("No email found for order buyer")

        success = brevo_send_message_file(
            to_email=order.buyer.email, html_content=msg_body, subject=subject, filepaths=[pdf_path], sender_name=business.name)
        # FIXME: this does not work
        db.order.update_one(
            {"id": ObjectId(order.id)}, {"$set": {"message_sent": success}})

        # send email to each attendee
        for index, ticket in enumerate(ticket_objs):
            # check if attendee has already been invited
            if ticket.message_sent is False or resend is True:
                # generate html with qr code
                subject, msg_body = format_ticket_invitation(
                    venue, business, ticket)

                ticket_filename = ""
                qr_filename = "/tmp/qr.png"
                generate_qr_code_png(ticket.id, qr_filename)
                if rendered_html is True:
                    # generate qr code from ticket id
                    ticket_filename = "tmp/" + \
                        ticket_data_array[index]["output_file"]

                # send email
                print("Sending email to", ticket.guest_details.email)
                print("Business name", business.name)
                success = brevo_send_message_file(
                    to_email=ticket.guest_details.email, html_content=msg_body, subject=subject,
                    filepaths=[ticket_filename, qr_filename], sender_name=business.name)
                # update attendee email_sent to true
                # sent_to_ids.append(ticket.id)
                db.attendee.update_one(
                    {"id": ObjectId(ticket.id)}, {"$set": {"message_sent": success}})

    # except Exception as e:
    #     print(e)
    #     print("Error sending email.")


@orders.get("/resend-emails/{order_id}")
async def send_confirmation_emails(background_tasks: BackgroundTasks,
                                   order_id: str, tenant_id: str = Header(...)):
    # check if order exists
    db = get_tenant_db(tenant_id, precheck=True)
    order = get_order(db, order_id)
    # from util.ticketgen import invite_order_tickets_task
    if order.payment_data.status == PaymentStatus.completed:
        background_tasks.add_task(
            invite_order_tickets_task, tenant_id, order_id, resend=True)
        return {"message": "Sending emails in background"}
    else:
        raise HTTPException(status_code=400, detail="Order not paid")


@orders.get("/ticket-tiers", response_model=list[TicketTier])
async def get_ticket_tiers(tenant_id: str = Header(...)):
    db = get_tenant_db(tenant_id, precheck=True)
    tiers = db.ticket_tiers.find()
    # convert to array of TicketTier objects
    # convert id to str
    tiers_obj = []
    for tier in tiers:
        tier['_id'] = str(tier['_id'])
        # if key param exists
        if 'enabled' in tier:
            if tier['enabled'] is False:
                continue
        tiers_obj.append(TicketTier(**tier))

    return tiers_obj


@orders.get("/download/{tenant_id}/{order_id}", response_class=StreamingResponse)
async def download_ticket(order_id: str, tenant_id: str):
    # get tenant db
    db = get_tenant_db(tenant_id, precheck=True)
    order = get_order(db, order_id)
    venue = get_venue(db, order.venue_id)

    HTML_RENDERED_TICKETS = True
    # get ticket ids and order items
    if HTML_RENDERED_TICKETS:
        from util.parsing import prepare_ticket_render_dictlist
        ticket_data = prepare_ticket_render_dictlist(order, venue)
    else:
        ticket_data = create_ticket_dict(order_id, order)

    from util.ticketgen import generate_ticket_order_pdf

    try:
        await generate_ticket_order_pdf(ticket_data, "tmp/tickets.pdf", rendered_html=HTML_RENDERED_TICKETS)
        pdf_stream = open("tmp/tickets.pdf", "rb")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error generating pdf")

    return StreamingResponse(content=pdf_stream, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=tickets.pdf"})


@orders.get("/info/{order_id}", response_model=Order)
async def get_order_info(order_id: str, tenant_id: str = Header(...)):
    db = get_tenant_db(tenant_id, precheck=True)
    order = get_order(db, order_id)
    return order


@orders.get("/info/{order_id}/tickets", response_model=list[TicketDisplay])
async def get_order_tickets(request: Request, order_id: str, tenant_id: str = Header(...)):
    ''' Gets tickets for an order in an easy to display iframe format '''
    db = get_tenant_db(tenant_id, precheck=True)
    order = get_order(db, order_id)
    tickets = []
    from config.config import root_prefix
    base_url = str(request.base_url) + root_prefix[1:]
    print(base_url)
    for item in order.order_items:
        iframe_url = f"{base_url}/tickets/{tenant_id}/{item.ticket_id}/iframe"
        ticket = TicketDisplay(
            **item.dict(), iframe_url=iframe_url, payment_method=order.payment_data.method)
        tickets.append(ticket)
    return tickets
