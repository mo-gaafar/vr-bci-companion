from fastapi import Depends
from pymongo import MongoClient
from .config import CONFIG
import ssl


# ssl_context = ssl.create_default_context()
# ssl_context.check_hostname = False
# ssl_context.verify_mode = ssl.CERT_NONE
uri = CONFIG.MONGO_URI
# Create a new client and connect to the server
conn = MongoClient(uri)

# Currently used database
MongoDB = conn[CONFIG.MONGO_DB]

if CONFIG.PRODUCTION == False:
    # Create a new database for testing
    MongoDB = conn[CONFIG.MONGO_DB_TEST]

if CONFIG.PRODUCTION == True:
    # Create a new database for production
    MongoDB = conn[CONFIG.MONGO_DB]

# Google Cloud Platform Image Database
# GCPBucket =

# Send a ping to confirm a successful connection
try:
    conn.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)


def get_mongo_db():
    return MongoDB
