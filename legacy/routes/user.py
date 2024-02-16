from datetime import datetime
from util.security import verify_token_header
from bson.objectid import ObjectId
from fastapi import APIRouter, Header, HTTPException, Form, UploadFile, File, Depends, Query
from util.multitenant import check_tenancy, get_tenant_db
from models.users import UserToken, BaseUser, UserInDB, UserOut
from util.security import split_passkey, generate_tokens, verify_hash_password, create_default_passkey

user = APIRouter(tags=["user"])


@user.get("/login/obtaintoken", response_model=UserToken)
async def login_token(tenant_id: str, passkey: str):
    try:
        # validate passkey
        username, password = split_passkey(passkey, validate=True)
        # get user from db
        db = get_tenant_db(tenant_id, precheck=True)
        user = db.users.find_one({"username": username})
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        # check password
        if not verify_hash_password(password, user["encrypted_pass"]):
            raise HTTPException(status_code=401, detail="Invalid password")
        # create jwt token
        user["_id"] = str(user["_id"])
        tokens = generate_tokens(UserOut(**user))
        # return user and token
        return tokens
    except:
        raise HTTPException(400, "Authentication Failed")


@user.get("/login/refreshtoken", response_model=UserToken)
async def refresh_token(tenant_id: str, refresh_token: str):
    '''Obtain token from refresh token and also renew refresh token'''
    # get user from db
    db = get_tenant_db(tenant_id, precheck=True)
    # decode refresh token and get user id
    from util.security import verify_token
    user = verify_token(refresh_token)
    # create jwt token
    tokens = generate_tokens(user)
    # return user and token
    return tokens


@user.post("/create", tags=["backend_admin"], response_model=UserOut)
async def create_user(tenant_id: str = Header(...), auth_user: UserOut = Depends(verify_token_header)):
    pass


@user.get("/all/credentials", tags=["backend_admin"], response_model=list[UserInDB])
async def get_all_default_credentials(tenant_id: str = Header(...), auth_user: UserOut = Depends(verify_token_header)):
    '''Get all default credentials for a tenant'''

    tenant_db = get_tenant_db(tenant_id, precheck=True)
    users = list(tenant_db.users.find())
    users_obj = []
    from util.security import create_default_passkey
    for user in users:
        user["_id"] = str(user["_id"])
        user["encrypted_pass"] = create_default_passkey(user["username"])
        user = UserInDB(**user)
        users_obj.append(user)

    return users_obj


@user.patch("/logout", tags=["backend_admin"])
async def logout_user(tenant_id: str = Header(...), auth_user: UserOut = Depends(verify_token_header)):
    # set valid_date to now
    db = get_tenant_db(tenant_id, precheck=True)
    db.users.update_one({"_id": ObjectId(auth_user.id)}, {
                        "$set": {"valid_date": datetime.utcnow()}})
