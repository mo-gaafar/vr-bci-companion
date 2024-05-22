import itertools
from typing import List, Optional, Protocol, runtime_checkable
import requests
from pydantic import BaseModel

from server.config import CONFIG

POSTMARK_API_URL = "https://api.postmarkapp.com"

# === Email Request Models ===


class EmailBase(BaseModel):
    email: str
    subject: str
    body: str


class EmailTemplateBase(EmailBase):
    template_alias: str
    template_model: dict


class ResetPassTemplate(BaseModel):
    product_url: str
    product_name: str
    name: str
    action_url: str
    operating_system: str
    browser_name: str
    support_url: str
    company_name: str
    company_address: str


class ResetPassEmailRequest(EmailTemplateBase):
    template_alias: str = "password-reset"  # Or your actual alias in Postmark
    template_model: ResetPassTemplate


# === Generic Email Client Interface ===
@runtime_checkable
class EmailClient(Protocol):
    sender_email: str

    def send_email(self, email: EmailBase, attachment: Optional[List[dict]] = None) -> dict:
        ...

    def send_template_email(self, email: EmailTemplateBase) -> dict:
        ...

    def send_bulk_email(self, emails: List[EmailBase], channel: str = "broadcast") -> None:
        ...


# === Postmark Client Implementation ===

class PostmarkClient(EmailClient):
    def __init__(self, api_key=CONFIG.POSTMARK_API_KEY, sender_email=CONFIG.POSTMARK_SENDER_EMAIL):
        self.api_key = api_key
        self.sender_email = sender_email  # Satisfies EmailClient requirement
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Postmark-Server-Token": self.api_key,
        }
        if not self.sender_email:
            raise ValueError(
                "POSTMARK_SENDER_EMAIL not found in configuration.")

    def _send_request(self, endpoint, payload, batch=False):
        url = f"{POSTMARK_API_URL}/{endpoint}"
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            error_msg = f"Exception when calling Postmark: {e}"
            if batch:
                # More specific for bulk
                error_msg = f"Exception in batch request: {e}"
            print(error_msg)
            return None

    def send_email(self, email: EmailBase, attachment: Optional[List[dict]] = None) -> dict:
        payload = {
            "From": self.sender_email,
            "To": email.email,
            "Subject": email.subject,
            "HtmlBody": email.body,
            "TextBody": email.body,  # Optional, include if you want plain text version
        }
        if attachment:
            payload["Attachments"] = attachment
        return self._send_request("email", payload)

    def send_template_email(self, email: EmailTemplateBase) -> dict:
        # convert template model to json
        from json import dumps
        template_payload = email.template_model.model_dump(
            exclude_unset=True)

        payload = {
            "From": self.sender_email,
            "To": email.email,
            "TemplateAlias": email.template_alias,
            "TemplateModel": template_payload,
        }
        return self._send_request("email/withTemplate", payload)

    def send_bulk_email(self, emails: List[EmailBase], channel="broadcast") -> None:
        max_per_batch = 400  # Postmark's limit
        for batch in (emails[i:i+max_per_batch] for i in range(0, len(emails), max_per_batch)):
            payload = [{"To": e.email, "From": self.sender_email, "Subject": e.subject,
                        "HtmlBody": e.body, "TextBody": e.body, "MessageStream": channel} for e in batch]
            self._send_request("email/batch", payload, batch=True)


# === Example Usage ===

def send_welcome_email(email_client: EmailClient, recipient: str, name: str):
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader('server/templates'))
    template = env.get_template('welcome_email.html')
    html_content = template.render(name=name)  # Render with user's name

    email = EmailBase(
        email=recipient,
        subject="Welcome to NeuroHike VR!",
        body=html_content
    )
    email_client.send_email(email)
