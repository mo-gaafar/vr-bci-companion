from dotenv import dotenv_values
# from dateutil import tz
# import pytz

DEVELOPMENT = False  # ! Change this to False when deploying
VERSION = "v1"
SECRET_KEY = "thisisaseriouscaseofmonkeybusiness"
TZ = "Africa/Cairo"
conf = dotenv_values(".env")


ADMIN_PASS = conf["ADMIN_PASS"]
# Server
try:
    conf["MONGO_URI"]
except KeyError:
    print("Using different method to get env variables")
    import os
    conf = dict(os.environ)


root_prefix = f"/api/{VERSION}"
