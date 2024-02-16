from __future__ import print_function

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
import base64
from config.config import conf

configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = conf['BREVO_API_KEY']
api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
    sib_api_v3_sdk.ApiClient(configuration))


def brevo_send_message_file(html_content: str, to_email: str, subject: str, filepaths: list[str], sender_name="Illusionaire"):
    '''Send a message with a pdf attachment'''
    attachment_items = []
    for filepath in filepaths:
        if filepath is "":
            continue
        with open(filepath, "rb") as file:
            encoded = base64.b64encode(file.read())
            # chunked_pdf = base64.encodebytes(encoded_pdf)
        # filename get from pdf_path
        filename = filepath.split("/")[-1]
        attachment_item = {
            "name": filename,
            "content": encoded.decode("utf-8")}
        attachment_items.append(attachment_item)

    return brevo_send_message(to_email, subject, html_content, attachment_items, sender_name)


def brevo_send_message(to_email, subject, body, attachment=None, sender_name="Illusionaire"):
    sender = {"name": f"{sender_name} - Passapp",
              "email": "illusionaire@tingoeg.com"}
    to = [{"name": "Invitee", "email": to_email}]

    try:

        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=to, html_content=body, sender=sender, subject=subject,
            attachment=attachment)  # invalid attachment passed in request

        api_response = api_instance.send_transac_email(send_smtp_email)
        print(api_response)
        return True
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)
        return False
