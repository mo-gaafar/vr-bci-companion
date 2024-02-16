from fastapi import APIRouter, Depends, Header, HTTPException, Form
from models.business import Plan, PlanIn
from repository.db import admin_db

from util.security import super_admin_auth
admin = APIRouter(dependencies=[Depends(super_admin_auth)], tags=['admin'])


@admin.post("/plan/create", response_model=Plan)
async def create_plan(plan: PlanIn):
    # check if plan already exists
    if admin_db.plans.find_one({"name": plan.name, "is_annual": plan.is_annual, "is_monthly": plan.is_monthly}) is not None:
        raise HTTPException(status_code=400, detail="Plan already exists")
    plan_id = admin_db.plans.insert_one(plan.dict()).inserted_id
    return Plan(**plan.dict(), _id=plan_id)

@admin.patch("/business/users/changepasswords", tags=["backend_admin"])
async def change_passwords():
    # TODO: change passwords of all users
    # logout all users
    