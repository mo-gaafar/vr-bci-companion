from fastapi import Body
from common.util.misc import db_to_dict
from auth.repo import get_auth_user_by_id, generate_otp
from auth.service import login, refresh_token_svc, logout
from typing import Optional
from database import MongoDB
from datetime import datetime
from common.util.security import verify_token_header, optional_token_header
from bson.objectid import ObjectId
from fastapi import APIRouter, Header, HTTPException, Form, UploadFile, File, Depends, Query
from auth.models import UserToken, BaseUser, UserInDB, UserOut, GenerateOTPResponse
from common.util.security import generate_tokens, verify_hash_password, get_token_header, verify_token

auth = APIRouter(prefix="/auth", tags=["auth"])

# TODO: POST /login/obtaintoken - obtain token
# TODO: POST /login/refreshtoken - obtain token from refresh token and also renew refresh token


@auth.post("/login/obtaintoken", response_model=UserToken)
async def login_token(username: str = Body(...), password: str = Body(...)):
    try:
        return login(username, password)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise HTTPException(e.status_code, str(e.detail))
        raise HTTPException(400, str(e))


@auth.post("/login/refreshtoken", response_model=UserToken)
async def refresh_token(refresh_token: Optional[str] = None, token: Optional[UserToken] = Depends(get_token_header)):
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
async def logout_user(auth_user: UserOut = Depends(verify_token_header)):
    try:
        logout(auth_user)
        return {"detail": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(400, str(e))


@auth.post("/headset/generateotp", response_model=GenerateOTPResponse)
async def generate_otp_for_headset(
    headset_id: str,
    auth_user: UserOut = Depends(verify_token_header)
):
    """Generates a One-Time Password (OTP) for a given headset and associates it with the logged-in user.

    Args:
        headset_id (str): The unique ID of the headset.
        auth_user (UserOut): The authenticated user information.

    Returns:
        GenerateOTPResponse: A response model containing the generated OTP and its estimated expiry time (in minutes).

    Raises:
        HTTPException: (401 Unauthorized) If the user is not authenticated.
    """
    user = get_auth_user_by_id(auth_user.id)  # Get user data
    otp_code = generate_otp(user, headset_id)
    return {"otp": otp_code, "expiry": 5}  # Return OTP and expiry in minutes


@auth.get("/headset/checkotp")
async def check_headset_otp(headset_id: str):
    # Retrieve the OTP associated with the headset ID
    user = MongoDB.authuser.find_one({"headset_id": headset_id})
    if not user:
        return {"message": "No OTP found"}

    user = UserInDB(**db_to_dict(user))

    # Check if OTP has expired
    if user.otp_expires_at < datetime.utcnow():
        return {"message": "OTP expired"}

    # Clear OTP from database (security best practice)
    MongoDB.authuser.update_one({"_id": ObjectId(user.id)}, {"$unset": {
        "otp_code": "",
        "otp_generated_at": "",
        "otp_expires_at": "",
        "headset_id": ""
    }})

    return {"otp": user.otp_code}


@auth.post("/headset/login")
def headset_login(otp_code: str, headset_id: str, username: str, password: str):
    # Find user by username and password
    user = MongoDB.authuser.find_one({"username": username})
    if user is None:
        raise HTTPException(
            status_code=401, detail="Invalid username or password")
    user = UserInDB(**db_to_dict(user))

    # Validate OTP and if it belongs to the headset
    if user.otp_code != otp_code or user.headset_id != headset_id:
        raise HTTPException(
            status_code=401, detail="Invalid OTP or headset ID")

    # Additional checks ...

    # Clear OTP fields, generate tokens, and return them
    # ...
