
import json
import hashlib
import requests
FAWRY_BASE_URL = 'https://atfawry.fawrystaging.com'  # Staging
# FAWRY_BASE_URL = 'https://atfawry.fawry.com' # Production
# importing the requests library
# importing Hash Library


def fawry_create_card_token(merchant_code, customer, card, save_card=False):
    """
    Create a card token for a customer
    :param merchant_code: Fawry merchant code
    :param customer: Customer object
    :param card: Card object

    :return: Card token
    """


    # defining a params dict for the parameters to be sent to the API
    PaymentData = {
        'merchantCode': merchant_code,
        'customerProfileId': customer._id,
        'customerMobile': customer.phone,
        'customerEmail': customer.email,
        'cardNumber': card.number,
        'cardAlias': card.alias,
        'expiryYear': card.expiry_year,
        'expiryMonth': card.expiry_month,
        'cvv': card.cvv,
        'enable3ds': True,
        'isDefault': True,
        'returnUrl': 'https://developer.fawrystaging.com',
    }

    # sending post request and saving the response as response object
    url = FAWRY_BASE_URL + '/ECommerceWeb/Fawry/payments/cardTokenization'
    status_request = requests.post(url=url, params=json.dumps(PaymentData))

    # extracting data in json format
    status_response = status_request.json()

    # extracting response status
    status = status_response['statusCode']

    return status_response['cardToken']


def fawry_charge_card_token(card_token, merchant , order):

    # Payment Data
    merchantCode    = merchant.merchant_code
    merchantRefNumber  = order.ref_number
    merchant_cust_prof_id  = order.customer._id
    payment_method = 'CARD'
    amount = order.amount
    cvv = 123
    returnUrl = 'https://www.google.com/'
    card_token = card_token
    merchant_sec_key =  merchant.merchant_sec_key
    signature = hashlib.sha256(merchantCode + merchantRefNumber + merchant_cust_prof_id + payment_method + amount + card_token + cvv + returnUrl + merchant_sec_key).hexdigest()

    # defining a params dict for the parameters to be sent to the API
    PaymentData = {
        'merchantCode' : merchantCode,
        'merchantRefNumber' : merchantRefNumber,
        'customerName' : 'Ahmed Ali',
        'customerMobile' : '01234567891',
        'customerEmail' : 'example@gmail.com',
        'customerProfileId' : '777777',
        'cardToken' : card_token,
        'cvv' : '123',
        'amount' : '580.55',
        'currencyCode' : 'EGP',
        'language' : 'en-gb',
        'chargeItems' : {
                            'itemId' : '897fa8e81be26df25db592e81c31c',
                            'description' : 'Item Description',
                            'price' : '580.55',
                            'quantity' : '1'
                        },
        'enable3DS' : true,
        'authCaptureModePayment' : false,
        'returnUrl' : 'https://www.google.com/',
        'signature' : signature,
        'paymentMethod' : 'CARD',
        'description': 'example description'
    }

    # sending post request and saving the response as response object
    status_request = requests.post(url = URL, params = json.dumps(PaymentData))

    # extracting data in json format
    status_response = status_request.json()