from fastapi import WebSocket
from fastapi import APIRouter, HTTPException, Path, Body
from .models import CalibrationStartResponse, ClassificationStartRequest, ClassificationStartResponse, ClassificationResult

bci = APIRouter(prefix="/bci", tags=["bci"])


@bci.post("/calibration/start", response_model=CalibrationStartResponse)
def start_calibration():
    # Implementation to initiate a calibration session
    return CalibrationStartResponse(...)


@bci.get("/calibration/status/{sessionId}", response_model=CalibrationStartResponse)
def fetch_calibration_status(sessionId: str = Path(..., description="The session ID of the calibration session")):
    # Fetch and return the status of the specified calibration session
    placeholder_walking_mi_protocol = [
        {"time": 0, "action": "Prepare"},
        {"time": 5, "action": "Start Imagining Walking"},
        {"time": 15, "action": "Stop and Rest"},
        {"time": 25, "action": "Repeat or End"},
    ]
    # check session start time
    return CalibrationStartResponse(message="Dummy calibration", sessionId=sessionId, protocol=placeholder_walking_mi_protocol, start_time="2021-01-01T00:00:00Z")


@bci.post("/classification/start", response_model=ClassificationStartResponse)
def start_classification(request: ClassificationStartRequest):
    # Start a classification session using the specified model
    return ClassificationStartResponse(...)


@bci.get("/classification/result/{sessionId}", response_model=ClassificationResult)
def fetch_classification_result(sessionId: str = Path(..., description="The session ID of the classification session")):
    # Fetch and return the latest classification result
    return ClassificationResult(...)


# open websocket in parallel with classification to stream data and save it

@bci.websocket("/stream/{sessionId}")
async def bci_websocket(websocket: WebSocket, sessionId: str = Path(..., description="The session ID of the calibration session")):
    # Open a WebSocket connection to stream data into the backend as long as the lsl stream is active
    # The WebSocket connection should be closed when the session is completed
    # accumulate signal in local cache for later processing with the classification model or any related processing
    while True:
        data = websocket.receive_text()
        if data == "close":
            await websocket.close()
            break
        else:
            await websocket.send_text(f"Message text was: {data}")
            # process data or save it to a file or database
            # for example, save the data to a file with epoch timestamps for each  sample

            with open(f"{sessionId}_data.txt", "a") as f:
                f.write(f"{data}\n")

    return
