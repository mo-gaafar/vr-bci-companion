import asyncio
import json
import random
import pytest
import websockets
from server.bci.models import LSLPacket

from tests.conftest import testapp  # Import your testapp fixture


async def send_fake_data(websocket):
    # Send fake data packets
    while True:
        for i in range(10000):  # Adjust the number of packets as needed
            sample = [random.random() for _ in range(8)]
            packet = LSLPacket(stream_id="test", timestamp=i, sample=sample)
            await websocket.send_json(packet.dict())
            await asyncio.sleep(0.1)  # Adjust sleep for real-time simulation


@pytest.mark.asyncio
async def test_bci_session(testapp):  # Use the 'testapp' fixture
    with testapp.websocket_connect("api/v1/bci/stream/test") as websocket:
        # Send handshake packet (START)
        await websocket.send_json({
            "type": "START",
            "session_id": "test",
            "channel_labels": ['T3', 'T4', 'C3', 'C4', 'O1', 'O2', 'P3', 'P4']
        })

        # Create an asyncio task to send data asynchronously
        send_task = asyncio.create_task(send_fake_data(websocket))

        # Check if the session is created while data is being sent
        response = testapp.get("api/v1/bci/sessions/")
        assert response.status_code == 200
        assert len(response.json()) > 0, "Session not created"

        # Add more assertions to verify the correctness of the data received and processed by your application.

        # Wait for the data sending task to complete
        await send_task

    # The 'with' block closing handles WebSocket closure gracefully


# @pytest.mark.usefixtures("testapp")
# def test_bci_session():
#     # step 1: starting sequence and handshake
#     # asyncio.run(send_fake_data())

#     # check if it creates a BCI session

#     # step 2: start streaming data to the websocket and check if the server receives it

#     # step 3 send an HTTP request in parallel to the server that should set the current session's mode to Calibration
#     # when that happens it should be accumulating data in the calibration buffer

#     # step 4: after calibration time is done it should stop accumulating and pickle the calibration data then clear
#     # the calibration buffer from the memory after storing the calibration data in the datalake as a pickle file

#     # check if step 4 is actually done and the calibration data is stored in the datalake

#     # step 5: train the model with the calibration data and store the model in the datalake
#     # note: while the model is being trained the session status will be set to training and any new data will be ignored

#     # check if the model is stored in the datalake
#     # check if the session status is set to training

#     # ? im thinking instead of discarding the buffer data we can store it in a timeseries  and then at the end of the session
#     # ? we can store the timeseries in the datalake as a pickle file (session meaning the calibration session or the classification session)

#     # step 6: while the websocket is still open and streaming data to the server,
#     # send an HTTP request to the server to set the session mode to classification and start classifying the data
#     # call the predict method of the trained model and return the predicted class to the client

#     # check if the session status is set to classification
#     # check if the predicted class is returned to the client

#     # step 7: close the websocket connection
#     # check if the session status is set to closed
#     # clear the calibration buffer and the classification buffer from the memory
