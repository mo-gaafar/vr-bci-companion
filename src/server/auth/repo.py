from common.exceptions import RepositoryException
from typing import Optional
from common.util.misc import check_empty
from .models import PairingCodeRecord
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
from datetime import datetime, timedelta, timezone


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


def get_user_by_token(token: str) -> UserInDB:
    # get user from db
    from common.util.security import get_user_from_token
    token = get_user_from_token(token)
    user = MongoDB.authuser.find_one({"_id": ObjectId(token.id)})
    return UserInDB(**db_to_dict(user))


def create_auth_user(user: UserIn):
    # check if user exists
    if MongoDB.authuser.find_one({"username": user.username}) is not None:
        raise RepositoryException("User already exists")
    # check if email exists
    if user.email is not None:
        if MongoDB.authuser.find_one({"email": user.email}) is not None:
            raise RepositoryException("Email already exists")
    # check if phone number exists
    if user.phone is not None:
        if MongoDB.authuser.find_one({"phone": user.phone}) is not None:
            raise RepositoryException("Phone number already exists")
    # create user
    user = UserInDB(**user.dict(), encrypted_pass=hash_password(user.password))
    id = MongoDB.authuser.insert_one(user.dict()).inserted_id
    user = MongoDB.authuser.find_one({"_id": id})

    return UserOut(**db_to_dict(user))


def create_pairing_code(user_id: str, device_id: str, code: str, generation_time, expiration) -> PairingCodeRecord:
    # check if pairing code for user or device exists and delete it
    record = MongoDB.pairingcodes.find_one({"user_id": user_id})
    if record is not None:
        MongoDB.pairingcodes.delete_one({"_id": record["_id"]})
        #  check if there are duplicate pairing codes
        record = MongoDB.pairingcodes.find({"code:": record["code"]})
        if check_empty(record) is False:
            raise RepositoryException(
                "Duplicated pairing code, regenerate code")

    record = PairingCodeRecord(
        user_id=user_id, device_id=device_id, code=code,
        generation_timestamp=generation_time, expiration_timestamp=expiration)
    id = MongoDB.pairingcodes.insert_one(record.model_dump()).inserted_id
    record = MongoDB.pairingcodes.find_one({"_id": id})
    return PairingCodeRecord(**record)


def get_pairing_code(code: str) -> PairingCodeRecord:
    # get pairing code from db
    record = MongoDB.pairingcodes.find_one({"code": code})
    return PairingCodeRecord(**db_to_dict(record))


def pair_user_to_device(user_id: str, device_id: str) -> None:
    # add user_id to pairing code
    result = MongoDB.pairingcodes.update_one({"device_id": device_id}, {
        "$set": {"user_id": user_id}})
    if result.matched_count == 0:
        raise RepositoryException("Pairing code not found")
    # add device_id to user
    MongoDB.authuser.update_one({"_id": ObjectId(user_id)}, {
        "$set": {"device_id": device_id}})

    # ? do i need to delete the pairing code after pairing? hmm


def check_if_headset_paired(device_id: str) -> ObjectId:
    '''Check if device_id is paired to a user_id and return user_id'''
    # check if device_id is paired
    record = MongoDB.pairingcodes.find_one({"device_id": device_id})
    return record["user_id"]


def fetch_user_by_device_id(device_id: str) -> UserOut:
    """Fetches the user associated with a given device ID."""
    user = MongoDB.authuser.find_one({"device_id": device_id})
    if user is None:  # Handle the case where no user is found
        raise RepositoryException("No user found for device ID")
    return UserOut(**db_to_dict(user))

# FIXME i think this belongs in service?


def validate_pairing(otp: str, device_id: Optional[str] = None, check_duplicate=True) -> PairingCodeRecord:
    """Validates if a device is paired and the pairing code is not expired."""

    record = MongoDB.pairingcodes.find_one(
        {"code": otp})

    if check_empty(record):
        raise RepositoryException("Device is not paired")
    if device_id is not None:  # checks device id if given
        record["device_id"] == device_id
    if record["user_id"] is not None:
        if check_duplicate:
            raise RepositoryException("Device is already paired")

    if record["expiration_timestamp"].replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise RepositoryException("Pairing code is expired")

    return PairingCodeRecord(**record)


def get_all_users(page: PaginationIn) -> PaginatedList[UserOut]:
    # get all users from db
    users = MongoDB.authuser.find().skip(
        page.skip).limit(page.limit)
    return PaginatedList(data=[UserOut(**db_to_dict(user)) for user in users], total=users.count())


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
