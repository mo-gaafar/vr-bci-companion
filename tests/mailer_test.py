import pytest
from server.common.util import mailing
from server.common.util.mailing import EmailBase, EmailClient, ResetPassEmailRequest, ResetPassTemplate, PostmarkClient


@pytest.mark.skip(reason="Subscription Expired")
@pytest.fixture(scope="module")
def mailing_client():
    from server.config import CONFIG
    client = PostmarkClient(api_key=CONFIG.POSTMARK_API_KEY,
                            sender_email=CONFIG.POSTMARK_SENDER_EMAIL)
    return client


@pytest.mark.skip(reason="Subscription Expired")
@pytest.mark.usefixtures("mailing_client")
def test_send_email(mailing_client):
    email_request = EmailBase(email="mohamednasser2001@gmail.com", subject="Test Email",
                              body="This is a test email")
    response = mailing_client.send_email(email_request)
    assert response is not None
    assert response.get("ErrorCode") == 0


@pytest.mark.skip(reason="Subscription Expired")
@pytest.mark.usefixtures("mailing_client")
def test_send_reset_password_email(mailing_client):
    # test send reset password email
    from server.common.util.mailing import ResetPassEmailRequest, ResetPassTemplate
    template_model_dict = ResetPassTemplate(product_url="https://neurohike.quest",
                                            product_name="NeuroHike VR",
                                            name="Test User",
                                            action_url="https://neurohike.quest/reset-password?token=token_value",
                                            operating_system="Test OS",
                                            browser_name="Edge",
                                            support_url="https://neurohike.quest/contact",
                                            company_name="NeuroHike VR",
                                            company_address="Cairo, Egypt")

    email_request = ResetPassEmailRequest(email="mohamednasser2001@gmail.com", subject="Reset Password",
                                          body="Reset Password", template_alias="password-reset",
                                          template_model=template_model_dict)

    response = mailing_client.send_template_email(email_request)
    assert response is not None
    assert response.get("ErrorCode") == 0
