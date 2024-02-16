# from __future__ import print_function

# # from email.message import EmailMessage
# from util.qrmail import generate_qr_code_png
# from email.mime.multipart import MIMEMultipart
# from email.mime.image import MIMEImage
# from email.mime.text import MIMEText
# import base64
# from config.config import conf

# import google.auth
# import google.oauth2.service_account
# from googleapiclient.discovery import build
# from googleapiclient.errors import HttpError

# # creds, _ = google.auth.default()
# # using service account
# creds = google.oauth2.service_account.Credentials.from_service_account_file(
#     conf['GOOGLE_APPLICATION_CREDENTIALS'], scopes=[
#         'https://mail.google.com/'],
#     subject=conf['MAIL_USERNAME']
# )


# def gmail_send_message(html_content: str, to_email: str, subject: str, attendee_id: str, plain_text: str):
#     """Create and send an email message
#     Print the returned  message id
#     Returns: Message object, including message id

#     Load pre-authorized user credentials from the environment.
#     TODO(developer) - See https://developers.google.com/identity
#     for guides on implementing OAuth2 for the application.
#     """

#     try:
#         service = build('gmail', 'v1', credentials=creds)
#         # message = EmailMessage()
#         message = MIMEMultipart()

#         message['to'] = to_email
#         message['from'] = conf['MAIL_USERNAME']
#         message['subject'] = subject

#         # Add html content to message
#         html_part = MIMEText(html_content, 'html')
#         message.attach(html_part)

#         # # Add plain text to message
#         # plain_text.replace('<br>', '\n')
#         # plain_part = MIMEText(plain_text, 'plain')
#         # message.attach(plain_part)

#         # generate qr code and attach to message
#         generate_qr_code_png(attendee_id, "EventPass.png")
#         # add image to message
#         with open('EventPass.png', 'rb') as f:
#             img = MIMEImage(f.read())
#             img.add_header('Content-ID', '<image1>')
#             message.attach(img)

#         # print(type(message))

#         encoded_message = base64.urlsafe_b64encode(
#             message.as_bytes()).decode()

#         create_message = {
#             'raw': encoded_message
#         }
#         # pylint: disable=E1101
#         send_message = (service.users().messages().send
#                         (userId="me", body=create_message).execute())
#         print(F'Message Id: {send_message["id"]}')
#         return True
#     except HttpError as error:
#         print(F'An error occurred: {error}')
#         # send_message = None
#         return False

# # if __name__ == '__main__':
# #     gmail_send_message()
