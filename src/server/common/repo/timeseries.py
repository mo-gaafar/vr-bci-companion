from fastapi import APIRouter, Depends, HTTPException
from pymongo import MongoClient, ASCENDING
from pymongo.database import Database
from config import CONFIG
from enum import Enum
import pickle

router = APIRouter()


class StorageType(str, Enum):
    MONGODB = "mongodb"
    LOCAL_FILE = "local_file"


def get_mongo_db():
    client = MongoClient(CONFIG.MONGO_URI)
    return client[CONFIG.MONGO_DB]

# Create or get the time series collection


@router.on_event("startup")
async def startup_event(db: Database = Depends(get_mongo_db)):
    db.create_collection(
        "eeg_data_time_series",
        timeseries={"timeField": "epoch_timestamp", "metaField": "metadata"},
    )
    db["eeg_data_time_series"].create_index([("epoch_timestamp", ASCENDING)])

# Endpoint for appending EEG data points


@router.post("/eeg_data/")
async def append_eeg_data(
    eeg_data: list[dict],
    storage_type: StorageType,
    session_id: str = None,  # Required if using MongoDB
    db: Database = Depends(get_mongo_db)
):
    if storage_type == StorageType.MONGODB:
        if not session_id:
            raise HTTPException(
                status_code=400, detail="Session ID is required for MongoDB storage")

        try:
            for data_point in eeg_data:
                data_point["metadata"] = {"session_id": session_id}
            collection = db["eeg_data_time_series"]
            result = collection.insert_many(eeg_data)
            return {"inserted_ids": [str(id) for id in result.inserted_ids]}
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error inserting data: {e}")

    elif storage_type == StorageType.LOCAL_FILE:
        try:
            filename = f"eeg_data_{session_id}.pkl" if session_id else "eeg_data.pkl"
            with open(filename, "ab") as f:
                pickle.dump(eeg_data, f)
            return {"message": f"Data appended to {filename}"}
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error appending data to file: {e}")

