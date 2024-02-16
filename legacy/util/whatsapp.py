

import requests
# Replace FROM_PHONE_NUMBER_ID and ACCESS_TOKEN with your actual values
from_phone_number_id = "your_from_phone_number_id"
access_token = "your_access_token"

def send_whatsapp_template_message(phone,template_id, access_token):
    endpoint = "https://graph.facebook.com/v17.0/" + from_phone_number_id + "/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone,
        "type": "template",
        "template": {
            "name": "TEMPLATE_NAME",
            "language": {
                "code": "LANGUAGE_AND_LOCALE_CODE"
            },
            "components": [
                {
                    "type": "header",
                    "parameters": [
                        {
                            "type": "image",
                            "image": {
                                "link": "http(s)://URL"
                            }
                        }
                    ]
                },
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": "TEXT_STRING"
                        },
                        {
                            "type": "currency",
                            "currency": {
                                "fallback_value": "VALUE",
                                "code": "USD",
                                "amount_1000": NUMBER
                            }
                        },
                        {
                            "type": "date_time",
                            "date_time": {
                                "fallback_value": "MONTH DAY, YEAR"
                            }
                        }
                    ]
                },
            ]
        }
    }

    response = requests.post(endpoint.replace("FROM_PHONE_NUMBER_ID", from_phone_number_id), headers=headers, json=payload)
    if response.status_code == 200:
        print("Template message sent successfully.")
    else:
        print("Failed to send template message.")
        print(response.json())



def get_whatsapp_message_status(message_id):
    """ Using meta's whatsapp API, get the status of a message """
