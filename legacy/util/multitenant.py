from fastapi import HTTPException, Header
from repository.db import admin_db, conn
from typing import Optional
from models.business import Business


def check_tenancy(tenant_id):
    '''Check if tenant exists in admin database, returns tenant if exists, otherwise none'''
    # check if tenant exists in admin database
    tenant = admin_db.business.find_one({'tenant_id': tenant_id})
    # check if database exists
    db_name = 'tenant_' + tenant_id
    if db_name not in conn.list_database_names():
        return None
    if tenant is None:
        return None
    return tenant


def create_tenant(business: Business):
    '''Create database in mongodb for business'''
    # check if tenant exists in admin database
    if check_tenancy(business.tenant_id) is not None:
        raise HTTPException(status_code=409, detail="Tenant already exists")
    # create new db
    db_name = 'tenant_' + business.tenant_id
    db = conn[db_name]
    # create new collections
    db.create_collection('venues')
    db.create_collection('customers')
    db.create_collection('tickets')
    db.create_collection('ticket_tiers')
    db.create_collection('orders')
    db.create_collection('users')

    # add placeholder data
    # db.venue.insert_one({'name': 'venue1', 'location': 'location1', 'maps_link': 'maps_link1'})
    # db.customer.insert_one({ 'name': 'customer1', 'phone': 'phone1', 'email': 'email1'})
    # db.ticket_tier.insert_one({'name': 'default', 'price': 100, 'description': 'description1', 'features': ['feature1', 'feature2']})

    # insert business into business collection in admin db
    admin_db.business.insert_one(business.dict())


def get_tenant_db(tenant_id, precheck=False):
    '''Get tenant database'''
    # check if tenant exists in admin database
    if precheck:
        tenant = check_tenancy(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=404, detail="Business not found")
    db_name = 'tenant_' + tenant_id
    db = conn[db_name]
    return db

# def get_tenant_db_from_user_token(user_token):
#     # get tenant id from user token
#     tenant_id = get_tenant_id_from_user_token(user_token)
#     # get tenant db
#     return get_tenant_db(tenant_id)
