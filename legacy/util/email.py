from fastapi_mail import FastMail, MessageSchema, ConnectionConfig


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from config.config import fm_conf
import smtplib

from fastapi import BackgroundTasks


def send_email(background_tasks: BackgroundTasks, reciepient, subject, content):

    message = MessageSchema(
        subject=subject,
        recipients=[reciepient],
        body=content,
        subtype="html"
    )

    fm = FastMail(fm_conf)
    background_tasks.add_task(fm.send_message, message)
