import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import CONFIG


class SMTPMailer:
    def __init__(self):
        self.smtp_server = CONFIG.SMTP_SERVER
        self.port = CONFIG.SMTP_PORT
        self.username = CONFIG.SMTP_USERNAME
        self.password = CONFIG.SMTP_PASSWORD.get_secret_value()
        print(self.smtp_server, self.port, self.username, self.password)

    def send_email(self, receivers, subject, body, is_html=False):
        try:
            msg = MIMEMultipart()
            msg["From"] = self.username
            msg["To"] = ", ".join(receivers)
            msg["Subject"] = subject

            if is_html:
                msg.attach(MIMEText(body, "html"))
            else:
                msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP_SSL(self.smtp_server, self.port, timeout=10) as server:
                server.login(self.username, self.password)
                server.sendmail(self.username, receivers, msg.as_string())
                print("Email sent successfully to", receivers)
        except Exception as e:
            print(f"Failed to send email. Error: {e}")

    def send_confirmation_email(self, recipient, confirmation_link):
        subject = "Account Confirmation"
        body = get_confirmation_mail_html(confirmation_link)

        self.send_email([recipient], subject, body, is_html=True)

    def send_notification_email(self, recipient, message):
        subject = "Notification"
        body = f"Hello,\n\n{message}"

        self.send_email([recipient], subject, body)

    def send_reset_password_email(self, recipient, reset_link):
        subject = "Reset Password"
        body = get_reset_password_mail_html(reset_link)

        self.send_email([recipient], subject, body, is_html=True)


def get_confirmation_mail_html(confirmation_link):
    return f"""
    <div style="background-color: #23272B; padding: 20px; border-radius: 10px; width: 500px; margin: 0 auto;">
        <h1 style="text-align: center; color: #FFFFFF;">Confirm your email</h1>
        <p style="text-align: center; color: #FFFFFF;">Please click the button below to confirm your email.</p>
        <a href={confirmation_link} style="text-decoration: none; display: block; margin: 0 auto; width: 200px; background-color: #17A2B8; color: #f2f2f2; padding: 10px; border-radius: 10px; text-align: center;">Confirm</a>
        <p style="text-align: center; color: #FFFFFF;">If you can't click on the button, please copy the following link to your browser</p>
        <p style="text-align: center; color: #17A2B8;">{confirmation_link}</p>
        <br>
        <p style="text-align: center; color: #FFFFFF;">Thank you for using our website</p>
        <p style="text-align: center; color: #FFFFFF;">The <a href="{APP_SETTINGS.CLIENT_DOMAIN}" style="text-decoration: none; color: #17A2B8;">{APP_SETTINGS.APP_NAME}</a> team</p>
        <hr style="border: 0.5px solid #FFFFFF; width: 100%; margin: 20px 0;">
        <p style="text-align: center; color: #FFFFFF;">If you didn't sign up for an account, you can safely delete this email</p>
    </div>
    """


def get_reset_password_mail_html(reset_link):
    return f"""
    <div style="background-color: #23272B; padding: 20px; border-radius: 10px; width: 500px; margin: 0 auto;">
        <h1 style="text-align: center; color: #FFFFFF;">Reset your password</h1>
        <p style="text-align: center; color: #FFFFFF;">Please click the button below to reset your password.</p>
        <a href={reset_link} style="text-decoration: none; display: block; margin: 0 auto; width: 200px; background-color: #17A2B8; color: #f2f2f2; padding: 10px; border-radius: 10px; text-align: center;">Reset password</a>
        <p style="text-align: center; color: #FFFFFF;">If you can't click on the button, please copy the following link to your browser</p>
        <p style="text-align: center; color: #17A2B8;">{reset_link}</p>
        <br>
        <p style="text-align: center; color: #FFFFFF;">Thank you for using our website</p>
        <p style="text-align: center; color: #FFFFFF;">The <a href="{APP_SETTINGS.CLIENT_DOMAIN}" style="text-decoration: none; color: #17A2B8;">{APP_SETTINGS.APP_NAME}</a> team</p>
        <hr style="border: 0.5px solid #FFFFFF; width: 100%; margin: 20px 0;">
        <p style="text-align: center; color: #FFFFFF;">If you didn't request to reset your password, you can safely delete this email</p>
    </div>
    """
