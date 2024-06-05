from server.auth.service import verify_token_header, optional_token_header
from typing import Optional
from datetime import datetime
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

@bci.get("/session/obtain/")
def obtain_session(auth_user=Depends(optional_token_header)):
    # Obtain a new session ID or the existing session ID for the user
    # session_id = session_manager.obtain_session()
    session_id = "12345678-1234-5678-1234-567812345678"
    return {"session_id": session_id}

@bci.get("/calibration/start/", response_model=CalibrationStartResponse)
def start_calibration(session_id: Optional[str] = Query(None, description="The session ID of the calibration session"),
                      auth_user=Depends(optional_token_header)):
    # Implementation to initiate a calibration session
    # check if session exists
    # session = session_manager.get_session(session_id)
    # if not session:
    #     raise HTTPException(status_code=404, detail="Session not found")

    # Placeholder Calibration protocol
    protocol = PLACEHOLDER_PROTOCOL
    # Start the calibration session and return the response
    # session.init_calibration(protocol)

    return CalibrationStartResponse(message="Dummy calibration started", session_id="1234", protocol=protocol, start_time="2021-01-01T00:00:00Z")


@bci.get("/classification/start/", response_model=ClassificationStartResponse)
def start_classification(request: ClassificationStartRequest, auth_user=Depends(optional_token_header),
                         session_id: str = Query(..., description="The session ID of the classification session")):
    # Start the classification mode and return the response
    try:
        session = session_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        try:
            session.init_classification(request)
            return ClassificationStartResponse(message="Classification started",
                                               session_id=request.session_id,
                                               start_time=datetime.now(),
                                               protocol=PLACEHOLDER_PROTOCOL,
                                               server="localhost")
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@bci.get("/classification/result/", response_model=ClassificationResult)
def fetch_classification_result(session_id: str = Query(..., description="The session ID of the classification session"),
                                auth_user=Depends(optional_token_header)):
    # Fetch and return the latest classification result
    return ClassificationResult(...)


# open websocket in parallel with classification to stream data and save it

@bci.websocket("/stream/{session_id}")
async def bci_websocket(session_id: str, websocket: WebSocket):
    from server.bci.streaming import bci_websocket as bci_websocket_stream
    # create a new session and start streaming data
    # create the session in the db

    await bci_websocket_stream(websocket, session_id)


@bci.get("/session/{location}/")
def get_sessions(session_state: SessionState = Query(None, description="Filter sessions by state", alias="state"),
                 session_id: str = Query(
                     None, description="Filter sessions by ID", alias="id"),
                 ):
    '''Get a list of sessions based on the query parameters. If no parameters are provided, all sessions are returned.
    If a session ID is provided, only the session with that ID is returned. If a session state is provided, only sessions with that state are returned.'''
    sessions = []
    if session_id and session_state:
        raise HTTPException(
            status_code=400, detail="Cannot filter by both session ID and state")

    if session_id:
        session = session_manager.get_session(session_id)
        if session:
            return session.__dict__()
        else:
            raise HTTPException(status_code=404, detail="Session not found")

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
