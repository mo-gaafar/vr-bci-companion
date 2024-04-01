
from secrets import token_hex  # For stronger randomness
import hashlib
import random
import time
from common.util.misc import id_to_str
from auth.models import UserInDB, UserOut, RoleEnum
from config import SECRET_KEY, DEVELOPMENT, ADMIN_PASS
import bcrypt
from auth.models import UserInDB, UserOut, UserToken
import jwt
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, Header
from typing import Optional

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


def super_admin_auth(admin_auth: str = Header(...)):
    if admin_auth != ADMIN_PASS:
        raise HTTPException(status_code=401, detail="Invalid authentication")


def access_check(user: UserOut, allowed_roles: list[RoleEnum], raise_exception: bool = True):
    allowed = True
    if user.role not in allowed_roles:
        allowed = False
    if not allowed:
        if raise_exception:
            raise HTTPException(
                status_code=403, detail="Access denied, you only have " + user.role + " access")
    return allowed


def get_token_header(authorization: Optional[HTTPAuthorizationCredentials] = Depends(optional_security)) -> Optional[UserToken]:
    if authorization is None:
        return None
    if authorization.scheme.lower() != "bearer":
        # raise Exception("Invalid token")
        return None
    else:
        return UserToken(auth_token=authorization.credentials, refresh_token=None)


def get_iat_from_token(token: str) -> datetime:
    # decode token
    payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    # get user from payload
    iat = payload.get("iat")
    # convert to datetime
    iat = datetime.utcfromtimestamp(iat) + timedelta(seconds=1)
    return iat


def verify_token(token: str, user: UserInDB) -> UserOut:
    try:
        token_user = get_user_from_token(token)

        if user.valid_date is not None:
            # check token is not expired
            print(get_iat_from_token(token))
            print(user.valid_date)
            if get_iat_from_token(token) < user.valid_date:
                raise Exception("Token expired")
        return token_user
    except jwt.ExpiredSignatureError:
        raise Exception("Token expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")


def validate_password(password: str) -> None:
    # validate password (should be 6 numbers)
    if not password.isnumeric():
        raise Exception("Password must be numbers only")
    if len(password) != 6:
        raise Exception("Password must be 6 digits")


def login_with_password(user: UserInDB, password: str) -> UserToken:
    # get password hash
    encrypted_pass = user["encrypted_pass"]
    # check password
    verify_hash_password(password, encrypted_pass)
    # generate tokens
    tokens = generate_tokens(UserOut(**user))
    return tokens


def create_defult_password(username: str):
    '''Generate a default passkey for a user'''
    # validate user (should be all lowercase no numbers)
    if not username.islower():
        raise Exception("Username must be lowercase")
    if not username.isalpha():
        raise Exception("Username must be letters only")
    # generate 6 digit number password from many letters in username
    password = ""
    for index, letter in enumerate(username):  # very secret algorithm
        # print(letter, ord(letter), index % 2)
        password += str(ord(letter[index % 1]))
    password = password[:6]
    return password


def get_user_from_token(token: str) -> UserOut:
    # decode token
    payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    # get user from payload
    user = id_to_str(payload.get("user"))
    user_out = UserOut(**user)

    return user_out


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode()


def verify_hash_password(password: str, encrypted_pass: str) -> bool:
    try:

        check = bcrypt.checkpw(password.encode(
            'utf-8'), encrypted_pass.encode('utf-8'))
        if not check:
            raise Exception("Invalid password")
        return check
    except Exception as e:
        return False


def generate_tokens(user: UserOut) -> UserToken:
    utcnow = datetime.utcnow()
    exp = utcnow + timedelta(minutes=15)
    access_token_payload = {
        'user': user.dict(),
        'exp': exp,  # Access token expiration time
        'iat': utcnow  # Access token issued at
    }
    access_token = jwt.encode(access_token_payload,
                              SECRET_KEY, algorithm='HS256')
    refresh_token_payload = {
        'user': user.dict(),
        'exp': datetime.utcnow() + timedelta(days=30),  # Refresh token expiration time
        'iat': datetime.utcnow()  # Refresh token issued at
    }
    refresh_token = jwt.encode(
        refresh_token_payload, SECRET_KEY, algorithm='HS256')

    return UserToken(auth_token=access_token, refresh_token=refresh_token)


def generate_token_from_refresh(refresh_token) -> UserToken:
    user = verify_token(refresh_token)
    if user is None:
        raise Exception("Invalid refresh token")

    access_token, _ = generate_tokens(user)
    user_token = UserToken(
        auth_token=access_token[0], refresh_token=refresh_token)
    return user_token


# --- PAIRING CODE GENERATION ---

def safe_int(char):
    if '0' <= char <= '9':
        return int(char)
    else:
        return 0  # Or handle the non-numeric character as you see fit


def generate_pairing_code(generation_timestamp: datetime, device_id: str):
    # Configuration (adjust as needed)
    code_length = 8
    random_digits = 5
    seed = 593982
    time_component_digits = 2
    checksum_digits = 1

    # 1. Strong Random Base
    random_part = token_hex(seed)[-random_digits:]

    # 2. Epoch Time Component
    current_epoch = int(generation_timestamp.timestamp())
    time_component = str(current_epoch % 10**time_component_digits)

    # 3. Incorporate Device ID
    device_id_str = str(device_id)
    pre_checksum = random_part + time_component + device_id_str

    # 4. Simple Checksum
    checksum = str(sum(map(safe_int, pre_checksum)))[-checksum_digits:]
    # 5. Assemble the Code
    code = random_part + time_component + checksum
    return code

# --- PAIRING CODE VERIFICATION ---


def verify_code(generation_timestamp: str, device_id: str, code: str) -> bool:

    # 2. Check Validity Window
    time_difference = int(time.time()) - \
        generation_timestamp.timestamp()
    if time_difference > 300:  # 5 minute validity TODO: fix this
        return False

    # 3. Regenerate Expected Code
    expected_code = generate_pairing_code(
        generation_timestamp, device_id)

    # 4. Compare
    return code == expected_code
