
# importing the requests library
import requests
import json
# importing Hash Library
import hashlib
from config.config import DEVELOPMENT

from models.orders import Order

if DEVELOPMENT:
    FAWRY_URL = "https://atfawry.fawrystaging.com"
else:
    FAWRY_URL = "https://atfawry.fawry.com"


def authenticate_fawry(user=None, passw=None, refresh_token=None):
    try:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        access_token = None
        if refresh_token is not None:
            # use refresh token to get new access token
            # FawryPay login API Endpoint
            URL = FAWRY_URL + "/user-api/auth/token/refresh/"
            # sending get request and saving the response as response object
            login_request = requests.post(
                url=URL, params=refresh_token, headers=headers)
            # extracting data in json format
            access_token = login_request.json()['token']
        elif user is not None and passw is not None:
            # use user and pass to get new access token
            URL = FAWRY_URL + "/user-api/auth/login/"
            # sending get request and saving the response as response object
            payload = {"userIdentifier": user, "password": passw}
            # json stringify
            login_request = requests.post(
                url=URL, params=json.dumps(payload), headers=headers)
            # extracting data in json format
            print(login_request.json())
            access_token = login_request.json()['token']
            refresh_token = login_request.json()['refreshToken']

        return access_token, refresh_token
    except Exception as e:
        print(e)
        return None, None

# def get_payment_link()


def initiate_payment(order: Order, api_key, *args):
    pass
