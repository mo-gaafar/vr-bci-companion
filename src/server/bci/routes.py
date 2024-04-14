from .models import EEGChunk
import json
from .service import session_manager  # import the session manager instance
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi import WebSocket
from fastapi import APIRouter, HTTPException, Path, Body
from .models import CalibrationStartResponse, ClassificationStartRequest, ClassificationStartResponse, ClassificationResult

bci = APIRouter(prefix="/bci", tags=["bci"])

PLACEHOLDER_PROTOCOL = [
    {"time": 10, "action": "Prepare"},
    {"time": 5, "action": "Start Imagining Walking"},
    {"time": 5, "action": "Passive Movement"},
    {"time": 5, "action": "Stop and Rest"},
    {"time": 5, "action": "Start Imagining Walking"},
    {"time": 5, "action": "Passive Movement"},
    {"time": 5, "action": "Stop and Rest"},
    {"time": 5, "action": "Start Imagining Walking"},
    {"time": 5, "action": "Passive Movement"},
    {"time": 5, "action": "Stop and Rest"},
    {"time": 5, "action": "Start Imagining Walking"},
    {"time": 5, "action": "Passive Movement"},
    {"time": 5, "action": "Stop and Rest"},
    {"time": 5, "action": "Start Imagining Walking"},
    {"time": 5, "action": "Passive Movement"},
    {"time": 5, "action": "Stop and Rest"},
    {"time": 5, "action": "Start Imagining Walking"},
    {"time": 5, "action": "Passive Movement"},
    {"time": 5, "action": "Stop and Rest"},
    {"time": 5, "action": "Start Imagining Walking"},
    {"time": 5, "action": "Stop and Rest"},
    {"time": 5, "action": "Repeat or End"},
]


@bci.get("/calibration/start", response_model=CalibrationStartResponse)
def start_calibration():
    # Implementation to initiate a calibration session
    return CalibrationStartResponse(message="Dummy calibration", sessionId="1234", protocol=PLACEHOLDER_PROTOCOL, start_time="2021-01-01T00:00:00Z")


@bci.get("/calibration/status/{sessionId}", response_model=CalibrationStartResponse)
def fetch_calibration_status(sessionId: str = Path(..., description="The session ID of the calibration session")):
    # Fetch and return the status of the specified calibration session

    # check session start time
    return CalibrationStartResponse(message="Dummy calibration", sessionId=sessionId, protocol=PLACEHOLDER_PROTOCOL, start_time="2021-01-01T00:00:00Z")


@bci.get("/classification/start", response_model=ClassificationStartResponse)
def start_classification(request: ClassificationStartRequest):
    # Start a classification session using the specified model
    return ClassificationStartResponse(...)


@bci.get("/classification/result/{sessionId}", response_model=ClassificationResult)
def fetch_classification_result(sessionId: str = Path(..., description="The session ID of the classification session")):
    # Fetch and return the latest classification result
    return ClassificationResult(...)


# open websocket in parallel with classification to stream data and save it


@bci.websocket("/stream/{session_id}")
async def bci_websocket(websocket: WebSocket, session_id: str = Path(..., description="The session ID of the calibration session")):
    '''Open a WebSocket connection to stream data into the backend as long as the lsl stream is active. The WebSocket connection should be closed when the session is completed. Accumulate signal in local cache for later processing with the classification model or any related processing.

    First frame should be the session ID. and Label for each channel. The following frames should be the EEG data.
    Frame 1: initial_frame = {
                "type": "START",
                "session_id": "1234",
                "channel_labels": ['T3', 'T4', 'C3', 'C4', 'O1', 'O2', 'P3', 'P4']
            }
    Frame 2: {"data": [1, 2, 3, 4, 5, 6, 7, 8],
                "timestamp": 1234567890}
    Frame End: {"type": "END"
                "session_id": "1234"
    }
    '''
    # Open a WebSocket connection to stream data into the backend as long as the lsl stream is active
    # The WebSocket connection should be closed when the session is completed
    # accumulate signal in local cache for later processing with the classification model or any related processing
    await websocket.accept()

    session_id = session_manager.create_session(
        session_id)  # Create a new session
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received data: {data}")
            session = session_manager.get_session(session_id)
            # Assume `data` is JSON or a format you can process
            data = json.loads(data)
            if data.get("type") == "END":
                raise WebSocketDisconnect
            if data.get("type") == "START":
                # Extract channel labels
                channel_labels = data.get("channel_labels")
                # Do something with the channel labels
                session.add_channel_labels(channel_labels)
                # send response to client
                await websocket.send_text(f"Received channel labels: {channel_labels}")
                await websocket.send_text("ACK")
                continue
            if session:
                # data = json.loads(data)
                # if 1D array, convert to 2D array
                print(data)
                data_chunk = EEGChunk(data=[data.get("data")], timestamp=[
                                      data.get("timestamp")])
                session.add_eeg_data(data_chunk)
                # send response to client
                await websocket.send_text(f"ACK_EEG {data.get('timestamp')}")
                print(f"Received data: {data}")
    except WebSocketDisconnect as e:
        # if close code is 1000 (normal closure), do not raise exception
        if e.code == 1000:
            print("Session ended by client")
        else:
            print("Session ended unexpectedly")
        # Handle disconnect
        session = session_manager.end_session(
            session_id, normal_closure=(e.code == 1000))
