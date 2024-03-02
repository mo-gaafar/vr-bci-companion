from services.subscription import check_subscription_of_authuser
from bson import ObjectId
from util.misc import db_to_dict
from abc import ABC, abstractmethod
from models.users import UserOut, UserInDB, UserIn
# from repo.auth_user import AuthUserRepository
from repo.db import MongoDB
from util.security import generate_tokens, get_iat_from_token, verify_hash_password, hash_password, verify_token
from util.misc import id_to_str, obj_to_dict
from datetime import datetime

REFRESH_TIME = 30  # days
ACCESS_TIME = 15  # minutes

INVALIDATE_PREVIOUS_TOKEN = True


def login(username: str, password: str) -> UserOut:
    # get user from db from username or email with priority to username
    user = MongoDB.authuser.find_one({"username": username})
    if user is None:
        user = MongoDB.authuser.find_one({"email": username})
    if user is None:
        raise Exception("Invalid username or email")
    # user = MongoDB.authuser.find_one({"username": username})
    user = UserInDB(**db_to_dict(user))
    # check password
    if not verify_hash_password(password, user.encrypted_pass):
        raise Exception("Invalid password")
    # check user is active
    if not user.is_active:
        raise Exception("Inactive user")
    # set valid_date to now
    if INVALIDATE_PREVIOUS_TOKEN:
        MongoDB.authuser.update_one({"_id": ObjectId(user.id)}, {
            "$set": {"valid_date": datetime.utcnow()}})

    check_subscription_of_authuser(UserOut(**obj_to_dict(user)))
    # create token
    return generate_tokens(UserOut(**obj_to_dict(user)))


def refresh_token_svc(refresh_token: str) -> UserOut:
    if refresh_token is None:
        raise Exception("Refresh token not provided")
    # get user from refresh token
    user = verify_token(refresh_token)
    # look up user in db
    print(user)
    user = db_to_dict(MongoDB.authuser.find_one({"_id": ObjectId(user.id)}))
    user = UserInDB(**user)
    # check if user is active and valid_date is not expired
    if not user.is_active:
        raise Exception("Inactive user")

    if user.valid_date is not None:
        print(get_iat_from_token(refresh_token))
        print(user.valid_date)
        if get_iat_from_token(refresh_token) < user.valid_date:
            raise Exception("User session expired")
    check_subscription_of_authuser(UserOut(**obj_to_dict(user)))
    # create token
    return generate_tokens(UserOut(**user.dict()))


def logout(auth_user: UserOut) -> None:
    # set valid date to now
    MongoDB.authuser.update_one({"_id": ObjectId(auth_user.id)}, {
        "$set": {"valid_date": datetime.utcnow()}})


# class BaseAuth(ABC):
#     @abstractmethod
#     def login(self, username: str, password: str) -> str:
#         raise NotImplementedError

#     @abstractmethod
#     def logout(self, username: str) -> None:
#         raise NotImplementedError

#     @abstractmethod
#     def refresh_token(self, refresh_token: str) -> str:
#         raise NotImplementedError

#     @abstractmethod
#     def verify_token(self, token: str) -> str:
#         raise NotImplementedError

#     @abstractmethod
#     def get_user_from_token(self, token: str) -> UserOut:
#         raise NotImplementedError

#     @abstractmethod
#     def get_user_from_refresh_token(self, refresh_token: str) -> UserOut:
#         raise NotImplementedError

#     @abstractmethod
#     def get_user_from_username(self, username: str) -> UserOut:
#         raise NotImplementedError

#     @abstractmethod
#     def get_user_from_email(self, email: str) -> UserOut:
#         raise NotImplementedError


# class JWTBearerAuthService(BaseAuth):
#     def __init__(self, auth_user_repo: AuthUserRepository):
#         self.secret_key = secret_key
#         self.algorithm = algorithm
#         self.access_token_expire_minutes = access_token_expire_minutes
#         self.refresh_token_expire_minutes = refresh_token_expire_minutes
#         self.auth_user_repo = auth_user_repo

#     def login(self, username: str, password: str) -> UserToken:
#         # get user from db
#         user = self.auth_user_repo.get_by_username(username)
#         # check password
#         if not self.auth_user_repo.verify_password(username, password):
#             raise Exception("Incorrect password")
#         # check user is active
#         if not user.is_active:
#             raise Exception("Inactive user")
#         # create token
#         return self.create_token(user)

#     def logout(self, username: str) -> None:
#         # get user from db
#         user = self.auth_user_repo.get_by_username(username)
#         # soft delete user
#         self.auth_user_repo.soft_delete(user)

#     def refresh_token(self, refresh_token: str) -> UserToken:
#         # get user from refresh token
#         user = self.get_user_from_refresh_token(refresh_token)
#         # create token
#         return self.create_token(user)

#     def verify_token(self, token: str) -> UserOut:
#         # get user from token
#         return self.get_user_from_token(token)

#     def get_user_from_token(self, token: str) -> UserOut:
#         # decode token
#         payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
#         # get user from db
#         return self.auth_user_repo.get_by_username(payload.get("sub"))

#     def get_user_from_refresh_token(self, refresh_token: str) -> UserOut:
#         # decode token
#         payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
#         # get user from db
#         return self.auth_user_repo.get_by_username(payload.get("sub"))

#     def get_user_from_username(self, username: str) -> UserOut:
#         # get user from db
#         return self.auth_user_repo.get_by_username(username)

#     def get_user_from_email(self, email: str) -> UserOut:
#         # get user from db
#         return self.auth_user_repo.get_by_email