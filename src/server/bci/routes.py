from fastapi import Query
from server.bci.streaming import bci_websocket
from server.bci.models import CalibrationAction, CalibrationSet, CalibrationProtocol
from server.bci.models import SessionState
import pickle
from fastapi import Depends
from pymongo import ASCENDING
from pymongo.database import Database
from server.common.repo.timeseries import StorageType, get_mongo_db
from .models import EEGChunk
import json
from .service import session_manager  # import the session manager instance
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi import WebSocket
from fastapi import APIRouter, HTTPException, Path, Body
from .models import CalibrationStartResponse, ClassificationStartRequest, ClassificationStartResponse, ClassificationResult

bci = APIRouter(prefix="/bci", tags=["bci"])

MAIN_TRIAL_SET = CalibrationSet(
    name="Main Trial Set", repeat=100, actions=[
        CalibrationAction(time=5, action="Start Imagining Walking"),
        CalibrationAction(time=5, action="Stop and Rest")
    ]
)
PLACEHOLDER_PROTOCOL = CalibrationProtocol(
    prepare=CalibrationSet(name="Prepare", repeat=1, actions=[
        CalibrationAction(time=5, action="Prepare for Calibration")
    ]),
    main_trial=MAIN_TRIAL_SET,
    end=CalibrationSet(name="End", repeat=1, actions=[
        CalibrationAction(time=5, action="End Calibration")
    ])
)


@bci.get("/calibration/start/{session_id}", response_model=CalibrationStartResponse)
def start_calibration(session_id: str = Path(..., description="The session ID of the calibration session")):
    # Implementation to initiate a calibration session

    return CalibrationStartResponse(message="Dummy calibration", sessionId="1234", protocol=PLACEHOLDER_PROTOCOL, start_time="2021-01-01T00:00:00Z")


@bci.get("/classification/start/{session_id}", response_model=ClassificationStartResponse)
def start_classification(request: ClassificationStartRequest):
    # Start the classification mode and return the response
    
    return ClassificationStartResponse(...)


@bci.get("/classification/result/{session_id}", response_model=ClassificationResult)
def fetch_classification_result(session_id: str = Path(..., description="The session ID of the classification session")):
    # Fetch and return the latest classification result
    return ClassificationResult(...)


# open websocket in parallel with classification to stream data and save it

@bci.websocket("/stream/{session_id}")
async def bci_websocket(session_id: str, websocket: WebSocket):
    from server.bci.streaming import bci_websocket as bci_websocket_stream
    await bci_websocket_stream(websocket, session_id)


@bci.get("/sessions")
def get_sessions(session_state: SessionState = Query(None, description="Filter sessions by state", alias="state"),
                 session_id: str = Query(
                     None, description="Filter sessions by ID", alias="id")
                 ):
    # ? TODO get by ID implementation
    sessions = []
    if not session_state:
        for session in session_manager.sessions:
            sessions.append(session.__dict__())

    if session_state:
        for session in session_manager.sessions:
            if session.state == session_state:
                sessions.append(session.__dict__())
    return sessions  # TODO: standardize this model into a pydantic schema later


@bci.get("/eeg_data/")
async def get_eeg_data(
    session_id: str,
    storage_type: StorageType,
    start_time: int = None,
    end_time: int = None,
    db: Database = Depends(get_mongo_db)
):
    if storage_type == StorageType.MONGODB:
        query = {"metadata.session_id": session_id}
        if start_time:
            query["epoch_timestamp"] = {"$gte": start_time}
        if end_time:
            query["epoch_timestamp"]["$lte"] = end_time

        cursor = db["eeg_data_time_series"].find(
            query).sort("epoch_timestamp", ASCENDING)
        return [{"magnitude": doc["magnitude"], "epoch_timestamp": doc["epoch_timestamp"]} for doc in cursor]

    elif storage_type == StorageType.LOCAL_FILE:
        filename = f"eeg_data_{session_id}.pkl" if session_id else "eeg_data.pkl"
        try:
            with open(filename, "rb") as f:
                all_data = []
                while True:
                    try:
                        all_data.extend(pickle.load(f))
                    except EOFError:
                        break
            return all_data
        except FileNotFoundError:
            raise HTTPException(
                status_code=404, detail=f"File not found: {filename}")
