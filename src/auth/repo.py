from auth.models import UserInDB, UserOut
from common.models import PaginationIn, PaginatedList
from pymongo import MongoClient
from abc import ABC, abstractmethod
# from repo import BaseRepository
from database import MongoDB
from common.util.misc import db_to_dict, obj_to_dict, id_to_str
from common.util.security import hash_password
from auth.models import UserIn, UserOut
from bson import ObjectId


def generate_otp(auth_user: UserOut) -> str:
    # generate otp
    return "123456"


def update_password(auth_user: UserOut, new_password: str) -> None:
    # update password
    MongoDB.authuser.update_one({"_id": ObjectId(auth_user.id)}, {
        "$set": {"encrypted_pass": hash_password(new_password)}})


def get_auth_user_by_email(email: str) -> UserOut:
    # get user from db
    user = MongoDB.authuser.find_one({"email": email})
    return UserOut(**db_to_dict(user))


def get_auth_user_by_username(username: str) -> UserOut:
    # get user from db
    user = MongoDB.authuser.find_one({"username": username})
    return UserOut(**db_to_dict(user))


def get_auth_user_by_id(user_id: str) -> UserOut:
    # get user from db
    user = MongoDB.authuser.find_one({"_id": ObjectId(user_id)})
    user = UserInDB(**db_to_dict(user))
    return UserOut(**user.dict())


def create_auth_user(user: UserIn):
    # check if user exists
    if MongoDB.authuser.find_one({"username": user.username}) is not None:
        raise Exception("User already exists")
    # check if email exists
    if user.email is not None:
        if MongoDB.authuser.find_one({"email": user.email}) is not None:
            raise Exception("Email already exists")
    # check if phone number exists
    if user.phone is not None:
        if MongoDB.authuser.find_one({"phone": user.phone}) is not None:
            raise Exception("Phone number already exists")
    # create user
    user = UserInDB(**user.dict(), encrypted_pass=hash_password(user.password))
    id = MongoDB.authuser.insert_one(user.dict()).inserted_id
    user = MongoDB.authuser.find_one({"_id": id})

    return UserOut(**db_to_dict(user))

# class AuthUserRepository(BaseRepository[UserInDB, UserOut], ABC):
#     @abstractmethod
#     def get_by_username(self, username: str) -> UserOut:
#         raise NotImplementedError

#     @abstractmethod
#     def get_by_id(self, _id: str) -> UserOut:
#         raise NotImplementedError

#     @abstractmethod
#     def soft_delete(self, user: UserInDB) -> UserOut:
#         raise NotImplementedError

#     @abstractmethod
#     def get_all(self, page: PaginationIn) -> PaginatedList[UserOut]:
#         raise NotImplementedError


# class MongoDBAuthUserRepository(AuthUserRepository):
#     def __init__(self, db: MongoClient):
#         self.db = db
#         self.collection = db['users']

#     def get_by_id(self, _id: str) -> UserOut:
#         return UserOut(**self.collection.find_one({"_id": _id}))

#     def create(self, user: UserInDB) -> UserOut:
#         self.collection.insert_one(user.dict())
#         return UserOut(**self.collection.find_one({"_id": user.id}))

#     def update(self, user: UserInDB) -> UserOut:
#         self.collection.update_one({"_id": user.id}, {"$set": user.dict()})
#         return UserOut(**self.collection.find_one({"_id": user.id}))

#     def delete(self, user: UserInDB) -> UserOut:
#         self.collection.delete_one({"_id": user.id})
#         return UserOut(**self.collection.find_one({"_id": user.id}))

#     def soft_delete(self, user: UserInDB) -> UserOut:
#         self.collection.update_one(
#             {"_id": user.id}, {"$set": {"is_active": False}})
#         return UserOut(**self.collection.find_one({"_id": user.id}))

#     def get_all(self) -> list[UserOut]:
#         return [UserOut(**user) for user in self.collection.find()]

#     def get_by_username(self, username: str) -> UserOut:
#         return UserOut(**self.collection.find_one({"username": username}))
