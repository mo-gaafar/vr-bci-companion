from bson import ObjectId
from abc import ABC, abstractmethod

from models.customer import CustomerInDB
from pymongo import MongoClient
from models.common import PaginationIn, PaginatedList
from repo.db import MongoDB

from repo.base import BaseRepository

from models.customer import CustomerInDB, CustomerSignupSuccess, CustomerForm

from util.misc import db_to_dict


def create_customer(customer_form: CustomerForm) -> CustomerSignupSuccess:
    # create customer
    customer_indb = CustomerInDB(**customer_form.dict())
    # check if customer already exists by email or phone
    customer = MongoDB.customer.find_one(
        {"$or": [{"phone": customer_indb.phone}]})
    if customer is not None:
        # customer already exists
        customer_db = CustomerInDB(**db_to_dict(customer))
        return CustomerSignupSuccess(customer_id=customer_db.id)

    customer_id = MongoDB.customer.insert_one(
        customer_indb.dict()).inserted_id
    return CustomerSignupSuccess(customer_id=str(customer_id))


def get_customer_by_id(customer_id: str) -> CustomerInDB:
    customer = MongoDB.customer.find_one({"_id": ObjectId(customer_id)})
    if customer is None:
        return None
    return CustomerInDB(**db_to_dict(customer))


def get_customers_by_ids(customer_ids: list[str]) -> list[CustomerInDB]:
    customers = MongoDB.customer.find(
        {"_id": {"$in": [ObjectId(customer_id) for customer_id in customer_ids]}})
    return [CustomerInDB(**db_to_dict(customer)) for customer in customers]

# class CustomerRepository(BaseRepository[CustomerInDB, CustomerOut], ABC):
#     pass


# class MongoDBCustomerRepository(CustomerRepository):
#     def __init__(self, db: MongoClient):
#         self.db = db
#         self.collection = self.db["customers"]

#     def get_by_id(self, _id: str) -> CustomerOut:
#         return self.collection.find_one({"_id": _id})

#     def create(self, obj: CustomerInDB) -> CustomerOut:
#         return self.collection.insert_one(obj)

#     def update(self, obj: CustomerInDB) -> CustomerOut:
#         return self.collection.update_one({"_id": obj["_id"]}, {"$set": obj})

#     def delete(self, obj: CustomerInDB) -> CustomerOut:
#         return self.collection.delete_one({"_id": obj["_id"]})

#     def get_all(self, page: PaginationIn) -> PaginatedList[CustomerOut]:
#         return PaginatedList(
#             data=self.collection.find().limit(page.limit).skip(page.skip),
#             total=self.collection.count_documents({}),
#         )
