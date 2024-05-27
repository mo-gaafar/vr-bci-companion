from server.bci.service import BCISession


import asyncio
import json
from typing import Dict, List

import mne
from mne.io import RawArray
import numpy as np
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
import uuid

from server.bci.models import (
    EEGChunk, SessionState
)
from server.bci.service import session_manager


'''
Use these payloads to test the WebSocket connection in the FastAPI application.
{
  "type": "START",
  "session_id": "12345678-1234-5678-1234-567812345678",
  "sampling_rate": "200",
  "channel_labels": [
    "T3",
    "T4",
    "C3",
    "C4",
    "O1",
    "O2",
    "P3",
    "P4"
  ]
}


{
  "type": "END",
  "session_id": "12345678-1234-5678-1234-567812345678"
}

{
  "type":"EEG_DATA",
  "timestamps": [1235123],
  "data": [[
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8
  ]]
}
'''


class StartMessage(BaseModel):
    """
    Represents the START message sent at the beginning of a WebSocket session.

    Attributes:
        type: Message type (always "START").
        session_id: Unique identifier for the session.
        channel_labels: List of channel labels corresponding to the EEG data.
        sampling_rate: Sampling rate of the EEG data.
    """
    type: str = Field(..., description="Message type (should be 'START')")
    session_id: uuid.UUID
    channel_labels: List[str]
    sampling_rate: float


class EndMessage(BaseModel):
    type: str = Field(..., description="Message type (should be 'END')")
    session_id: uuid.UUID


async def bci_websocket(websocket: WebSocket, session_id: uuid.UUID):
    """
    WebSocket endpoint for handling EEG data streaming.

    This function:
    1. Accepts a WebSocket connection.
    2. Creates a new BCI session or retrieves an existing one.
    3. Starts an asynchronous task to receive data from the WebSocket.
    4. Handles START, EEG_DATA, and END messages.

    Args:
        websocket: The WebSocket object representing the connection.
        session_id: Unique identifier for the session.
    """
    await websocket.accept()
    session = session_manager.create_session(session_id)
    await websocket.send_json({"message": "Session created", "session_id": str(session_id)})

    try:
        while True:
            data_str = await websocket.receive_text()
            print(data_str)
            data = json.loads(data_str)
            if data.get("type") == "START":
                handle_start_message(data, session)
            elif data.get("type") == "EEG_DATA":
                handle_eeg_data(data, session)
            elif data.get("type") == "END":
                await handle_end_message(data, session, websocket)
                break
            else:
                await websocket.send_json({"error": "Unknown message type"})
            await websocket.send_text("ACK")
    except WebSocketDisconnect:
        session_manager.end_session(session.session_id)


def handle_start_message(data: Dict, session: BCISession):
    """
    Handles START messages received from the WebSocket.

    This function:
    1. Parses the START message into a `StartMessage` object.
    2. Initializes the session with the received channel labels and sampling rate.
    3. Creates an empty `RawAr,ray` to store the incoming EEG data.
    """
    start_msg = StartMessage(**data)
    session.info = mne.create_info(
        ch_names=start_msg.channel_labels,
        sfreq=start_msg.sampling_rate,
        ch_types=["eeg"] * len(start_msg.channel_labels),
    )
    # session.raw = RawArray(
    #     np.zeros((len(session.channel_labels), 0)), info=session.info, verbose=False
    # )

    print(f"Session {session.session_id} started.")


def handle_eeg_data(data: Dict, session: BCISession):
    eeg_data_msg = EEGChunk(**data)
    session.add_eeg_data(eeg_data_msg)


async def handle_end_message(data: Dict, session: BCISession, websocket: WebSocket):
    end_msg = EndMessage(**data)
    session_manager.end_session(end_msg.session_id)
    stats = session.get_session_stats()
    await websocket.send_json(stats)
    await websocket.send_text("Session ended")
    await websocket.close()

    print(f"Session {session.session_id} ended.")
