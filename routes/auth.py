from services.auth import login, refresh_token_svc, logout
from typing import Optional
from datetime import datetime
from util.security import verify_token_header, optional_token_header
from bson.objectid import ObjectId
from fastapi import APIRouter, Header, HTTPException, Form, UploadFile, File, Depends, Query
from models.users import UserToken, BaseUser, UserInDB, UserOut
from util.security import generate_tokens, verify_hash_password, get_token_header, verify_token

auth = APIRouter(prefix="/auth", tags=["auth"])

# TODO: POST /login/obtaintoken - obtain token
# TODO: POST /login/refreshtoken - obtain token from refresh token and also renew refresh token


@auth.get("/login/obtaintoken", response_model=UserToken)
async def login_token(username: str, password: str):
    try:
        return login(username, password)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise HTTPException(e.status_code, str(e.detail))
        raise HTTPException(400, str(e))


@auth.get("/login/refreshtoken", response_model=UserToken)
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


@auth.patch("/logout", tags=["backend_admin"])
async def logout_user(auth_user: UserOut = Depends(verify_token_header)):
    try:
        logout(auth_user)
        return {"detail": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(400, str(e))
