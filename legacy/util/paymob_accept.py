from models.orders import Order
from models.customer import Customer
from config.config import conf

# Payment API Flow
import requests

def authenticate_paymob(api_key: str):

    url = "https://accept.paymob.com/api/auth/tokens"

    payload = {"api_key": api_key + "=="}
    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)

    return response.json()["token"]


def create_order(order: Order, token):

    url = "https://accept.paymob.com/api/ecommerce/orders"

    items_array = []
    # summarize order items and group based on ticket tier
    for item in order.order_items:
        if item.ticket_tier_price is None:
            raise Exception("Ticket tier price is None")
        items_array.append({
            "name": item.ticket_tier_name,
            "amount_cents": item.ticket_tier_price * 100,
            "description": item.ticket_tier_name,
            "quantity": 1
        })

    payload = {
        "auth_token":  token,
        "delivery_needed": "false",
        "amount_cents": order.payment_data.total_amount * 100,
        "currency": "EGP",
        "merchant_order_id": order.id,
        "items": items_array,
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code not in [200, 201]:
        raise Exception(response.json())

    return response.json()["id"]


def create_payment_key(order: Order, transaction_order_id: str, integration_id, token: str):

    url = "https://accept.paymob.com/api/acceptance/payment_keys"

    payload = {
        "auth_token": token + "==",
        "amount_cents": str(order.payment_data.total_amount*100),
        "expiration": 3600,
        "order_id": transaction_order_id,
        "billing_data": {
            "apartment": "NA",
            "email": order.buyer.email,
            "floor": "NA",
            "first_name": order.buyer.name.split(" ")[0],
            "street": "NA",
            "building": "NA",
            "phone_number": order.buyer.phone,
            "shipping_method": "NA",
            "postal_code": "NA",
            "city": "NA",
            "country": "NA",
            "last_name": (lambda: order.buyer.name.split(" ")[1] if len(order.buyer.name.split(" ")) > 1 else "")(),
            "state": "NA"
        },
        "currency": "EGP",
        "integration_id": integration_id,
        "lock_order_when_paid": "true"
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code not in [200, 201]:
        print(response.json())
        raise Exception(response.json())

    return response.json()["token"]


def get_payment_link(payment_key: str, frame_id: str):
    return "https://accept.paymob.com/api/acceptance/iframes/{}?payment_token={}".format(frame_id, payment_key)


def initiate_payment(order: Order, api_key, integration_id, frame_id):
    # api_key = "ZXlKaGJHY2lPaUpJVXpVeE1pSXNJblI1Y0NJNklrcFhWQ0o5LmV5SmpiR0Z6Y3lJNklrMWxjbU5vWVc1MElpd2ljSEp2Wm1sc1pWOXdheUk2T0RJMU16Z3lMQ0p1WVcxbElqb2lNVFk0TnpVeU1EVTFOUzR3TkRVME1USWlmUS42am1KanplT0E4Tmw3WjEwVDRsZjZDdkV6Vl9Ea2N2MUZsaS1NdzI3a0JQTXB1MkFJVlg5WmxHNkN5NThJazR3OXdYVFM1VWpvSEZsRHZiNHFRQk96QQ=="
    # 1. authentication request
    access_token = authenticate_paymob(api_key)

    # 2. order registration request
    trx_order_id = create_order(order, access_token)

    # 3. payment key request
    payment_key = create_payment_key(
        order=order, transaction_order_id=trx_order_id, integration_id=integration_id, token=access_token)

    return get_payment_link(payment_key, frame_id), trx_order_id
