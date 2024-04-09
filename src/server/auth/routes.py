from datetime import datetime, timezone, timedelta
from bson.objectid import ObjectId
from fastapi import APIRouter, Header, HTTPException, Form, UploadFile, File, Depends, Query
from typing import Annotated
from pydantic import EmailStr
from typing import Optional
from fastapi import Body
from .models import ResetPasswordRequest

from server.auth.repo import get_auth_user_by_id
from server.common.util.misc import db_to_dict
from server.auth.service import login, refresh_token_svc, logout, verify_token_header
from server.auth.models import UserToken, BaseUser, UserInDB, UserOut, GenerateOTPResponse
from server.common.models import BaseResponse
from server.common.util.security import generate_tokens, verify_hash_password, get_token_header, verify_token

auth = APIRouter(prefix="/auth", tags=["auth"])

# TODO: POST /login/obtaintoken - obtain token
# TODO: POST /login/refreshtoken - obtain token from refresh token and also renew refresh token


@auth.post("/login/obtaintoken", response_model=UserToken)
def login_token(username: str = Body(...), password: str = Body(...)):
    try:
        return login(username, password)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise HTTPException(e.status_code, str(e.detail))
        raise HTTPException(400, str(e))


@auth.post("/login/refreshtoken", response_model=UserToken)
def refresh_token(refresh_token: Optional[str] = None, token: Optional[UserToken] = Depends(get_token_header)):
    '''Obtain token from refresh token or HTTPBearer and also renew refresh token'''
    if refresh_token is None:
        # get refresh token from header
        if token is None:
            raise HTTPException(
                status_code=401, detail="Token not provided")

        refresh_token = token.refresh_token
    try:

        return refresh_token_svc(refresh_token)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise HTTPException(e.status_code, str(e.detail))
        raise HTTPException(400, str(e))


@auth.delete("/logout", tags=["backend_admin"])
def logout_user(auth_user: UserOut = Depends(verify_token_header)):
    try:
        logout(auth_user)
        return {"detail": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(400, str(e))


# TODO: Will be redirected to the frontend
@auth.get("/confirm/{token}", response_model=BaseResponse[None])
def confirm_email(email: EmailStr, token: str):
    # auth_service.confirm_email(email, token)
    return {"status": "success", "message": "Email confirmed successfully", "data": None}


@auth.post("/resend-confirmation-email", response_model=BaseResponse[None])
def resend_confirmation_email(email: EmailStr):
    # await auth_service.resend_confirmation_email(email)
    return {"status": "success", "message": "Confirmation email resent successfully", "data": None}


@auth.post("/forgot-password", response_model=BaseResponse[None])
def forgot_password(email: EmailStr):
    # auth_service.forgot_password(email)
    return {"status": "success", "message": "Password reset link sent successfully", "data": None}

# request body will contain token and new password and email


@auth.post("/reset-password", response_model=BaseResponse[None])
def reset_password(request: ResetPasswordRequest):
    # auth_service.reset_password(
    #     request.email, request.token, request.new_password)
    return {"status": "success", "message": "Password reset successfully", "data": None}


@auth.get("/users/me/", response_model=BaseResponse[UserOut])
def read_users_me(
    current_user: Annotated[UserOut, Depends(verify_token_header)]
):
    return {"status": "success", "message": "User details retrieved successfully", "data": current_user}


@auth.get("/headset/generateotp", response_model=GenerateOTPResponse)
def generate_otp_for_headset(
    headset_id: str
):
    """Generates a One-Time Password (OTP) for a given headset.
    Note: To get the headset id (serial) in unity use: \n
        AndroidJavaObject jo = new AndroidJavaObject("android.os.Build"); \n
        string deviceID = jo.GetStatic<string>("SERIAL"); \n

    Args:
        headset_id (str): The unique ID of the headset.
        auth_user (UserOut): The authenticated user information.

    Returns:
        GenerateOTPResponse: A response model containing the generated OTP and its estimated expiry time (in minutes).

    Raises:
        HTTPException: (401 Unauthorized) If the user is not authenticated.
    """

    # 1. Generate OTP
    from common.util.security import generate_pairing_code
    generation_time = datetime.now(timezone.utc)
    otp_code = generate_pairing_code(
        generation_timestamp=generation_time, device_id=headset_id)
    # 2. store it in the database
    from auth.repo import create_pairing_code
    record = create_pairing_code(user_id=None, device_id=headset_id,
                                 code=otp_code, generation_time=generation_time, expiration=generation_time + timedelta(minutes=5))
    # 3. Return the OTP and its expiry time
    return GenerateOTPResponse(otp=otp_code, expiry=5, pairing_id=record.id)


# a route to enter the otp on the website


@auth.post("/enterotp", response_model=BaseResponse[str])
def enter_otp_for_headset(
        body: dict = {"code": "example"}, auth_user: UserOut = Depends(verify_token_header)):
    """Enters the One-Time Password (OTP) for a given headset.
    Args:
        otp (str): The OTP to enter.
    Returns:
        BaseResponse[str]: A response model containing the status of the operation.
    Raises:
        HTTPException: (401 Unauthorized) If the user is not authenticated.
    """
    try:
        # 1. check if the user is authenticated
        from common.util.security import access_check
        access_check(auth_user, ["admin", "patient"])
        # 2. Check if the OTP is valid
        from auth.repo import get_pairing_code, pair_user_to_device, validate_pairing
        otp = body.get("code")
        if otp is None:
            raise HTTPException(422, "Wrong body format")
        pairing_code = validate_pairing(device_id=auth_user.device_id, otp=otp)
        # 3. Pair the headset with the user
        pair_user_to_device(user_id=auth_user.id,
                            device_id=pairing_code.device_id)

        # 4. Return the status of the operation

        return BaseResponse(data="Headset paired successfully")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise HTTPException(e.status_code, str(e.detail))
        raise HTTPException(400, "Failed to pair headset, " + str(e))


@auth.post("/headset/login/obtaintoken", response_model=UserToken)
def headset_obtain_token(headset_id: str, otp: str):
    """ Obtain token for the headset to use for authentication.
    Note that this can be done only once for a given OTP.
    You should use the usual refresh token endpoint to renew the token."""
    from auth.service import get_user_from_pairing
    try:
        user = get_user_from_pairing(headset_id, otp)
        return generate_tokens(user)
    except Exception as e:
        raise HTTPException(400, str(e))
