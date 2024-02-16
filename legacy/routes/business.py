from util.security import verify_token_header, access_check, super_admin_auth
from models.users import RoleEnum
from util.security import verify_token_header, access_check
from fastapi import APIRouter, Header, HTTPException, Form, UploadFile, File, Depends, Query
from typing import Annotated, Optional
from bson.objectid import ObjectId
from util.multitenant import get_tenant_db, create_tenant, check_tenancy
from datetime import datetime
from util.aws_s3 import base64_to_s3
from models.business import Business, Subscription, Plan, Venue, BusinessDetails, BusinessPreLogin
from models.tickets import TicketTier
from models.users import UserOut, UserIn, UserInDB
from config.config import pytz_timezone
from repository.db import admin_db


business = APIRouter(tags=["business"])


# ------------------ Business ------------------ #
@business.patch("/create", response_model=Business, tags=["backend_admin"])
def logout_all_users(tenant_id: str):
    # set all users to logged out
    db = get_tenant_db(tenant_id, precheck=True)
    db.users.update_many({}, {"$set": {"valid_date": datetime.utcnow()}})


def create_subscription(plan_name: str, subscription_end: datetime, tenant_id: str):
    '''Create subscription for business'''

    # FIXME check plan name and get plan id from admin db
    plan = admin_db.plans.find_one({'name': plan_name})
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    plan_id = str(plan['_id'])
    # plan_id = 'placeholder'

    # prepare subscription object
    subscription = Subscription(tenant_id=tenant_id, start_date=datetime.utcnow(),
                                end_date=subscription_end, is_active=True, is_trial=False, plan_name=plan_name,
                                plan_id=plan_id)  # type: ignore
    # create subscription in admin db
    subscription_id = admin_db.subscriptions.insert_one(
        subscription.dict()).inserted_id
    return subscription_id


def create_default_users(business_id: str, append: str = ""):
    '''Create default users for business'''

    # create default users
    users = [UserIn(username="admin", email="default@gmail.com", phone="0123456789", password="default", is_active=True, role=RoleEnum.admin, tenant_id=business_id, venue_id=None),
             UserIn(username="manager", email="default@gmail.com", phone="0123456789", password="default",
                    is_active=True, role=RoleEnum.manager, tenant_id=business_id, venue_id=None),
             UserIn(username="cashier", email="default@gmail.com", phone="0123456789",
                    password="default", is_active=True, role=RoleEnum.cashier, tenant_id=business_id, venue_id=None),
             UserIn(username="gatekeeper", email="default@gmai.lcom", phone="0123456789",
                    password="default", is_active=True, role=RoleEnum.gatekeeper, tenant_id=business_id, venue_id=None),
             UserIn(username="barista", email="default@gmail.com", phone="0123456789", password="default", is_active=True, role=RoleEnum.barista, tenant_id=business_id, venue_id=None)]

    # convert to UserInDB after hashing password
    # FIXME hashing password not implemented
    users = [UserInDB(**user.dict()) for user in users]
    from util.security import hash_password, create_defult_password
    for user in users:
        user.encrypted_pass = hash_password(
            create_defult_password(user.username))
    # insert users into tenant db
    tenant_db = get_tenant_db(business_id)
    tenant_db.users.insert_many([user.dict() for user in users])

    print("Default users created")


def create_default_tickettiers(business_id: str, def_venue_id: str):
    '''Create default ticket tiers for business'''

    # create default ticket tiers
    ticket_tiers = [
        TicketTier(
            name="Regular", price=100, business_id=business_id, venue_id=def_venue_id)  # type: ignore
    ]

    # insert ticket tiers into tenant db
    tenant_db = get_tenant_db(business_id)
    tenant_db.ticket_tiers.insert_many(
        [ticket_tier.dict() for ticket_tier in ticket_tiers])

    print("Default ticket tiers created")


def create_default_venue(business_id: str):
    '''Create default venue for business'''

    # create default venue
    venue = Venue(name="Default", business_id=business_id)  # type: ignore

    # insert venue into tenant db
    tenant_db = get_tenant_db(business_id)
    venue_id = tenant_db.venues.insert_one(venue.dict()).inserted_id

    print("Default venue created")
    return str(venue_id)


@business.post("/register/form", tags=["backend_admin"], dependencies=[Depends(super_admin_auth)])
async def register_business_from_form(name: str = Form(...), email: str = Form(...), phone: str = Form(...), logo: UploadFile = File(...), payment_secret: str = Form(...),
                                      payment_public: str = Form(...), subscription_end: datetime = Form(...), plan_name: str = Form(...),
                                      tenant_id: str = Header(...)):

    # convert image to link and store in s3
    # logo_link = base64_to_s3(logo)

    # check if business already exists
    if check_tenancy(tenant_id) is not None:
        raise HTTPException(status_code=400, detail="Business already exists")
    try:
        # create subscription
        subscription_id = str(create_subscription(
            plan_name, subscription_end, tenant_id))  # type: ignore

        # create business object
        locals_dict = locals()
        print(locals_dict)

        # print({k: locals_dict[k] for k in Business.__fields__})
        business = Business(
            **locals_dict, is_active=True)

        # allocate tenant db and create business
        create_tenant(business)

        create_default_users(business.tenant_id)
        def_venue_id = create_default_venue(business.tenant_id)
        create_default_tickettiers(business.tenant_id, def_venue_id)
        return {"message": "Business registered successfully", "subscription_id": subscription_id, "tenant_id": business.tenant_id}
    except Exception as e:
        print(e)
        # delete subscription if business creation fails
        admin_db.subscriptions.delete_one({"_id": ObjectId(subscription_id)})
        # delete tenant db if business creation fails
        # delete_tenant(business.tenant_id)
        raise HTTPException(status_code=500, detail="Internal server error")


@business.get("/details/", response_model=BusinessDetails)
async def get_business_details(tenant_id: str = Header(...), auth_user: UserOut = Depends(verify_token_header)):
    # check if business exists
    tenant = check_tenancy(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Business not found")
    if tenant["is_active"] is False:
        raise HTTPException(status_code=400, detail="Business is inactive")
    # get business details
    tenant_db = get_tenant_db(tenant_id)
    business = tenant_db.business.find_one({"tenant_id": tenant_id})
    # get current plan
    subscription = admin_db.subscriptions.find_one(
        {"tenant_id": tenant_id, "is_active": True})
    if subscription is None:
        raise HTTPException(status_code=404, detail="Subscription not found")
    plan_id = ObjectId(subscription["plan_id"])
    plan = admin_db.plans.find_one({"_id": plan_id})
    # print("Plan id" + subscription["plan_id"])
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")

    venues = list(tenant_db.venues.find({}))
    venues_obj = []
    for venue in venues:
        venue["_id"] = str(venue["_id"])
        # print(venue)
        venue = Venue(**venue)
        # print(venue.dict())
        venues_obj.append(venue)
    # tenant["_id"] = str(tenant["_id"])
    tenant.pop("_id")
    business_details = BusinessDetails(
        **tenant, plan_name=plan["name"], plan_features=plan["features"], subscription_end=subscription["end_date"], venues=venues_obj)
    print("Business found")
    return business_details


# ------------------ Venues ------------------ #
# TODO: create a new venue (FORM)


@business.post("/create/venue", tags=["backend_admin"])
async def add_venue(name: str = Form(...), location: str = Form(...), maps_link: str = Form(...), tenant_id: str = Header(...), auth_user: UserOut = Depends(verify_token_header)):
    access_check(auth_user, tenant_id, [RoleEnum.admin, RoleEnum.manager])
    # check if business exists
    tenant = check_tenancy(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Business not found")

    # add venue to business
    tenant_db = get_tenant_db(tenant_id)
    venue = Venue(name=name, location=location,
                  maps_link=maps_link, business_id=tenant_id)  # type: ignore
    venue_id = tenant_db.venues.insert_one(venue.dict()).inserted_id
    return {"message": "Venue added successfully", "venue_id": venue_id}

# @business.post("/venue/create/form", tags=["backend_admin"])
# async def create_venue(name: Annotated[str, Form(...)], location: Annotated[str, Form(...)], maps_link: Annotated[str, Form(...)]):
#     pass


@business.post("/create/ticket-tier", tags=["backend_admin"])
async def add_ticket_tier(name: str = Form(...), price: int = Form(...), max_quantity: int = Form(...), description: str = Form(...), tenant_id: str = Header(...), auth_user: UserOut = Depends(verify_token_header)):
    db = get_tenant_db(tenant_id, precheck=True)
    tier = TicketTier(name=name, price=price, max_quantity=max_quantity,
                      description=description, business_id=tenant_id)
    tier_id = db.ticket_tiers.insert_one(tier.dict()).inserted_id
    return {"tier_id": str(tier_id)}
# # TODO: change business subscription plan (FORM)
# @business.post("/subscription/update/form", tags=["backend_admin"])
# async def update_subscription(business_id: Annotated[str, Form(...)], plan_id: Annotated[str, Form(...)]):
#     pass

# # TODO: delete venue


@business.get("/prelogin/", tags=["backend_admin"], response_model=BusinessPreLogin)
async def prelogin(tenant_id: str = Header(...)):
    tenant = check_tenancy(tenant_id)

    return BusinessPreLogin(**tenant)
