from fastapi import Depends
from pymongo import MongoClient
from config.config import conf
import ssl


# ssl_context = ssl.create_default_context()
# ssl_context.check_hostname = False
# ssl_context.verify_mode = ssl.CERT_NONE
uri = conf['MONGO_URI']
# Create a new client and connect to the server
conn = MongoClient(uri)

# Currently used database
MongoDB = conn[conf['MONGO_DB']]

if conf['PRODUCTION'] == 'False':
    # Create a new database for testing
    MongoDB = conn[conf['MONGO_DB_TEST']]

if conf['PRODUCTION'] == 'True':
    # Create a new database for production
    MongoDB = conn[conf['MONGO_DB_PROD']]

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
