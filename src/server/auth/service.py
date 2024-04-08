# from services.subscription import check_subscription_of_authuser
from pydantic import EmailStr
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Optional
from fastapi import HTTPException, Depends
from bson import ObjectId
from abc import ABC, abstractmethod
from datetime import datetime

# from repo.auth_user import AuthUserRepository
from server.config import DEVELOPMENT
from server.auth.models import RoleEnum
from server.auth.repo import validate_pairing, fetch_user_by_device_id
from server.auth.models import UserOut
from server.auth.repo import get_user_by_token
from server.auth.models import UserOut, UserInDB, UserIn
from server.database import MongoDB
from server.common.util.security import generate_tokens, get_iat_from_token, verify_hash_password, hash_password, verify_token, optional_security, security
from server.common.util.security import verify_token
from server.common.util.misc import db_to_dict
from server.common.util.misc import id_to_str, obj_to_dict

REFRESH_TIME = 30  # days
ACCESS_TIME = 15  # minutes

INVALIDATE_PREVIOUS_TOKEN = True


def login(username: str, password: str) -> UserOut:
    # get user from db from username or email with priority to username
    user = MongoDB.authuser.find_one({"username": username})
    if user is None:
        user = MongoDB.authuser.find_one({"email": username})
    if user is None:
        raise Exception("Invalid username or email")
    # user = MongoDB.authuser.find_one({"username": username})
    user = UserInDB(**db_to_dict(user))
    # check password
    if not verify_hash_password(password, user.encrypted_pass):
        raise Exception("Invalid password")
    # check user is active
    if not user.is_active:
        raise Exception("Inactive user")
    # set valid_date to now
    if INVALIDATE_PREVIOUS_TOKEN:
        MongoDB.authuser.update_one({"_id": ObjectId(user.id)}, {
            "$set": {"valid_date": datetime.utcnow()}})

    # check_subscription_of_authuser(UserOut(**obj_to_dict(user)))
    # create token
    return generate_tokens(UserOut(**obj_to_dict(user)))


def refresh_token_svc(refresh_token: str) -> UserOut:
    if refresh_token is None:
        raise Exception("Refresh token not provided")
    # get user from refresh token
    # get valid_date from db
    user = get_user_by_token(refresh_token)
    user = verify_token(refresh_token, user)
    # look up user in db
    print(user)
    user = db_to_dict(MongoDB.authuser.find_one({"_id": ObjectId(user.id)}))
    user = UserInDB(**user)
    # check if user is active and valid_date is not expired
    if not user.is_active:
        raise Exception("Inactive user")

    if user.valid_date is not None:
        print(get_iat_from_token(refresh_token))
        print(user.valid_date)
        if get_iat_from_token(refresh_token) < user.valid_date:
            raise Exception("User session expired")
    # check_subscription_of_authuser(UserOut(**obj_to_dict(user)))
    # create token
    return generate_tokens(UserOut(**user.dict()))


def logout(auth_user: UserOut) -> None:
    # set valid date to now
    MongoDB.authuser.update_one({"_id": ObjectId(auth_user.id)}, {
        "$set": {"valid_date": datetime.utcnow()}})


def verify_token_header(authorization: HTTPAuthorizationCredentials = Depends(security)) -> UserOut:
    if DEVELOPMENT:
        return UserOut(**{
            "username": "admin",
            "role": RoleEnum.admin,
            "tenant_id": "test",
            "first_name": "Admin",
            "last_name": "Admin",
            "email": "admin@admin.com"})
    try:
        # check scheme is bearer
        if authorization.scheme.lower() != "bearer":
            raise Exception("Invalid token")
        # check token is valid
        user = get_user_by_token(authorization.credentials)
        return verify_token(authorization.credentials, user)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


def optional_token_header(authorization: HTTPAuthorizationCredentials = Depends(optional_security)) -> Optional[UserOut]:
    try:
        return verify_token_header(authorization)
    except Exception as e:
        return None


def confirm_email(email: str, token: str):
    # user = UsersDB().get_user(email)
    # if not decode_access_token(token).get("username") == user.username:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
    #     )
    # user.disabled = False
    # UsersDB().update_user(user)
    pass


def resend_confirmation_email(email: EmailStr):
    # user = UsersDB().get_user(email)
    # if not user.disabled:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="This account has already been verified",
    #     )
    # await send_confirmation_email(user)
    pass


def send_confirmation_email(user: UserOut):
    # print("Sending confirmation email")
    # mailer = Mailer()
    # confirmation_token = create_access_token(data=user.model_dump())
    # confirmation_link = f"{APP_SETTINGS.APP_DOMAIN}/auth/confirm/{confirmation_token}?email={user.email}"
    # mailer.send_confirmation_email(user.email, confirmation_link)
    pass


def forgot_password(email: EmailStr):
    # user = UsersDB().get_user(email)
    # if user.disabled:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="This account has not been verified yet, please confirm your account first",
    #     )
    # mailer = Mailer()
    # reset_token = create_access_token(data=user.model_dump())

    # reset_link = (
    #     f"{APP_SETTINGS.CLIENT_DOMAIN}/reset-password/{reset_token}?email={user.email}"
    # )
    # mailer.send_reset_password_email(user.email, reset_link)
    pass


def reset_password(email: EmailStr, token: str, new_password: str):
    # user = UsersDB().get_user(email)
    # if not decode_access_token(token).get("username") == user.username:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
    #     )
    # user.hashed_password = get_password_hash(new_password)
    # UsersDB().update_user(user)
    # Mailer().send_notification_email(
    #     user.email, "Your password has been reset successfully"
    # )
    pass


def get_user_from_pairing(device_id: str, otp: str) -> UserOut:
    """Gets the user from a valid pairing code."""
    pairing = validate_pairing(
        device_id=device_id, otp=otp, check_duplicate=False)
    from common.util.security import verify_code
    verify_code(pairing.generation_timestamp, pairing.device_id, pairing.code)
    return fetch_user_by_device_id(device_id)
