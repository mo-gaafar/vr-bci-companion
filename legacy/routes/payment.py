from fastapi import Depends
from models.users import RoleEnum
from util.security import verify_token_header, access_check
from models.users import UserOut
from repository.business import get_business
from repository.orders import get_order
import os
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Header
from fastapi.responses import RedirectResponse, HTMLResponse
# from models.common import ObjId
from bson.objectid import ObjectId
from models.orders import Order, PaymentStatus
from typing import Optional
from datetime import datetime
from models.business import Business
from models.customer import Customer
from models.tickets import Ticket
from util.multitenant import get_tenant_db
from repository.db import admin_db
import hashlib

payment = APIRouter(tags=["payment"])

#! TODO: verify hmac IMPORTANT FOR SECURITY


def verify_hmac(hmac, params, hmac_secret):
    # Get the shared HMAC secret from the environment variables
    hmac_secret = "?"

    # Concatenate the query parameters into a string
    params_str = ""
    for key in sorted(params.keys()):
        params_str += f"{key}={params[key]}&"

    # Remove the trailing '&' character
    params_str = params_str[:-1]

    # Calculate the HMAC
    calculated_hmac = hmac.new(
        hmac_secret.encode("utf-8"),
        msg=params_str.encode("utf-8"),
        digestmod=hashlib.sha512
    ).hexdigest()

    # Compare the calculated HMAC with the received HMAC
    return hmac == calculated_hmac


async def pay_order(background_tasks: BackgroundTasks, tenant_id, new_status: PaymentStatus,
                    order_id=None, order: Optional[Order] = None) -> Order:
    # from routes.orders import get_order
    from repository.orders import get_order
    db = get_tenant_db(tenant_id)
    if order is None:
        if order_id is None:
            raise HTTPException(status_code=400, detail="No order id provided")
        else:
            order = get_order(db, order_id)

    current_status = order.payment_data.status
    if current_status == new_status:
        raise HTTPException(
            status_code=400, detail="Order already {}".format(new_status))
    if current_status == PaymentStatus.completed:
        # latch on complete and dont fail if already completed
        if new_status == PaymentStatus.refunded:
            # raise not implemented
            order.payment_data.status = PaymentStatus.refunded
            # send confirmation refund email
            # deactivate tickets
            raise HTTPException(
                status_code=501, detail="Refund not implemented")
        if new_status == PaymentStatus.voided:
            # raise not implemented
            order.payment_data.status = PaymentStatus.voided
            # send confirmation refund email
            # deactivate tickets
            raise HTTPException(status_code=501, detail="Void not implemented")
    elif current_status == PaymentStatus.pending or current_status == PaymentStatus.failed:
        if new_status == PaymentStatus.completed:
            print("Transaction completed, sending emails")
            order.payment_data.status = PaymentStatus.completed
            order.payment_data.date_completed = datetime.utcnow()
            db.orders.update_one({"_id": ObjectId(order.id)}, {
                "$set": {"payment_data": order.payment_data.dict()}})
        else:
            # dont do anything
            pass
    elif current_status == PaymentStatus.refunded or current_status == PaymentStatus.cancelled:
        raise HTTPException(
            status_code=400, detail="Order already cancelled/refunded")
    else:
        raise HTTPException(status_code=400, detail="Invalid payment status")

    # update order
    print("Updating order" + str(order.id) +
          " status to " + str(order.payment_data.status))
    db.orders.update_one({"_id": ObjectId(order.id)}, {
        "$set": {"payment_data": order.payment_data.dict()}})

    # propagate to tickets
    db.tickets.update_many({"order_id": order.id},
                           {"$set": {"is_valid": order.payment_data.status ==
                                     PaymentStatus.completed}},
                           upsert=True)

    # messaging and notifications
    if order.payment_data.status == PaymentStatus.completed:
        from routes.orders import send_confirmation_emails
        await send_confirmation_emails(background_tasks, order.id, tenant_id)
        # send sms
        # send whatsapp

    return order


@payment.post("/cash/manual", description="Manual cash payment")
async def manual_cash_payment(background_tasks: BackgroundTasks, order_id: str, override_payment: bool = Query(False), tenant_id: str = Header(...), auth_user: UserOut = Depends(verify_token_header)):
    try:
        access_check(auth_user, tenant_id, [
            RoleEnum.admin, RoleEnum.cashier, RoleEnum.manager])

        from routes.orders import get_order
        #! TODO: verify authorization header
        # TODO: override payment not implemented
        from models.payment import PaymentMethod
        from repository.orders import get_order
        db = get_tenant_db(tenant_id, precheck=True)
        order = get_order(db, order_id)
        if order.payment_data.method != PaymentMethod.cash:
            raise HTTPException(
                status_code=400, detail="Order not eligible for cash payment")
        order = await pay_order(background_tasks, tenant_id, PaymentStatus.completed,
                                order=order)
        return {"message": "Cash payment processed successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Unknown error processing payment")


@payment.post("/processed/paymob", description="Paymob payment processed callback")
async def payment_response(background_tasks: BackgroundTasks, data: dict, hmac: str = Query(...)):
    # get tenant db
    if data is None:
        raise HTTPException(status_code=400, detail="Invalid request")

    obj = data["obj"]
    # print(obj)
    business = admin_db.business.find_one(
        {"payment_merchant_id": str(obj["profile_id"])})

    if business is None:
        raise HTTPException(status_code=400, detail="Business not found")

    # get HMAC secret from db
    # hmac_secret = business["payment_secret"]
    # if hmac_secret is None:
    #     return {"message": "HMAC secret not found"}

    # # verify HMAC
    # if not verify_hmac(hmac = hmac, hmac_secret=hmac_secret, params_dict=req):
    #     return {"message": "Invalid HMAC"}

    tenant_id = business["tenant_id"]
    new_status = PaymentStatus.pending
    if obj["is_refund"] == True:
        new_status = PaymentStatus.refunded
    elif obj["success"] == True:
        new_status = PaymentStatus.completed
    elif obj["is_voided"] == True:
        new_status = PaymentStatus.voided
    elif obj["is_refunded"] == True:
        new_status = PaymentStatus.refunded
    else:
        new_status = PaymentStatus.failed

    updated_order = await pay_order(background_tasks, tenant_id,
                                    new_status, order_id=obj["order"]["merchant_order_id"])

    return {"message": "Payment status updated successfully"
            "new status: {}".format(updated_order.payment_data.status)}


@payment.get("/link/{tenant_id}/{order_id}/")
async def retrieve_payment_link(order_id: str, tenant_id: str):
    # get tenant db
    db = get_tenant_db(tenant_id, precheck=True)
    # get order

    order = get_order(db, order_id)
    if order.payment_data.status == PaymentStatus.completed:
        raise HTTPException(status_code=400, detail="Order is already paid")

    business = get_business(tenant_id)
    from models.payment import PaymentMethod
    if order.payment_data.method == PaymentMethod.card:
        api_key = business.payment_api_key
        integration_id = business.payment_integration_id
        frame_id = business.payment_frame_id
        if api_key is None or integration_id is None or frame_id is None:
            raise HTTPException(
                status_code=400, detail="Business not configured for card payments")
        # get payment link from paymob
        from util.paymob_accept import get_payment_link, create_payment_key, authenticate_paymob, create_order
        access_token = authenticate_paymob(api_key=api_key)
        if order.payment_data.transaction_id is None:
            # create order again
            # not implemented error response
            trx_id = create_order(order, access_token)
            order.payment_data.transaction_id = trx_id
        payment_key = create_payment_key(
            order, order.payment_data.transaction_id, integration_id, access_token)
        payment_link = get_payment_link(
            payment_key=payment_key, frame_id=frame_id)
        return RedirectResponse(payment_link, status_code=302)

    if order.payment_data.method == PaymentMethod.cash:
        from util.ticketgen import generate_qr_code_html
        order_id_qr_tag = generate_qr_code_html(order.id)
        html = f"""
                    <html>
                        <head>
                            <title>Pay cash</title>
                            <style>
                                button{{
                                    background-color: green;
                                    border: none;
                                    color: white;
                                    padding: 15px 32px;
                                    text-align: center;
                                    text-decoration: none;
                                    border-radius: 12px;
                                    display: inline-block;
                                    font-size: 16px;
                                }}
                                button[disabled] {{
                                    cursor: not-allowed;
                                    opacity: 0.5;
                                }}
                                body {{
                                    background-color: #133337;
                                    color: white;
                                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                                    font-size: 18px;
                                    line-height: 1.5;
                                    margin: 0;
                                    padding: 50px 20px;
                                    display: flex;
                                    justify-content: center;
                                    align-items: center;
                                    height: 100vh;
                                }}
                                .container {{
                                    background-color: black;
                                    border-radius: 10px;
                                    padding: 30px;
                                    max-width: 600px;
                                    text-align: center;
                                }}
                                h3 {{
                                    font-size: 24px;
                                    margin-bottom: 20px;
                                }}
                                p {{
                                    margin-bottom: 10px;
                                    text-align: left;
                                }}
                                ul {{
                                    margin-bottom: 20px;
                                    padding-left: 40px;
                                    text-align: left;
                                }}
                                li {{
                                    margin-left: -20px;
                                }}
                                .qr-code {{
                                    max-width: 100%;
                                    height: auto;
                                    margin: 0 auto;
                                    display: flex;
                                    justify-content: center;
                                    align-items: center;
                                }}
                                img {{
                                    max-width: 100%;
                                    height: auto;
                                }}
                            </style>
                        </head>
                        <body>
                            <div class="container">
                                <h3>Pay cash</h3>
                                <p>Pay cash to the delivery person</p>
                                <p>Order ID: {order.id}</p>
                                <p>Amount: {order.payment_data.total_amount} {order.payment_data.currency}</p>
                                <p>Order items:</p>
                                <ul>
                                    {"".join([f"<li>{item.ticket_tier_name}</li>" for item in order.order_items])}
                                </ul>
                                <p>The cashier will scan the QR code below to confirm payment</p>
                                <p>Take a screenshot of this page and show it to the cashier</p>
                                <br>
                                <br>
                                <div class="qr-code">
                                    {order_id_qr_tag}
                                </div>
                                <br>
                                <br>
                                        <button id="my-button" onclick="handleButtonClick()">Download Order</button>
                                <script>
                                function handleButtonClick() {{
                                    const button = document.getElementById('my-button');

                                    // Construct the download URL with the path parameters
                                    const downloadUrl = `/api/v1/orders/download/{tenant_id}/{order.id}/`;

                                    // Navigate to the download URL
                                    window.location.href = downloadUrl;
                                    
                                    button.disabled = true;
                                    button.textContent = 'Downloading...';
                                    setTimeout(function() {{
                                                            button.disabled = false;
                                                            button.textContent = 'Download Order';
                                                            }}, 5000); // Adjust the delay as needed
                                    }}
                                    
                                </script>
                            </div>
                        </body>
                    </html>
                """
        return HTMLResponse(content=html, status_code=200)
