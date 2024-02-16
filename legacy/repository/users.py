# from bson.objectid import ObjectId
# from models.user import User
# from util.multitenant import get_tenant_db

from fastapi import APIRouter, Depends, HTTPException
from repository.db import admin_db
from models.users import UserOut

from bson.objectid import ObjectId
from util.multitenant import get_tenant_db, check_tenancy


def get_user(user_id: str, db=None, tenant_id=None):
    if db is None:
        db = get_tenant_db(tenant_id, precheck=True)
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user["_id"] = str(user["_id"])

    return UserOut(**user)
