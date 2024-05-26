import asyncio
import random
import pytest
from server.bci.models import EEGChunk

# Use a new UUID for each test
SESSION_ID = "12345678-1234-5678-1234-567812345678"

# @pytest.fixture(scope="module")
# async def bci_websocket(testapp):
    
#     uri = f"api/v1/bci/stream/{SESSION_ID}"
#     async with websockets.connect(testapp.url + uri) as ws:
#         yield ws

#     # Close the websocket connection after the test
#     await ws.close()

    
#TODO: send real EEG data from a local file or a known source
async def send_fake_data(websocket):
    # Send fake data packets
    while True:
        for i in range(10000):  # Adjust the number of packets as needed
            sample = [random.random() for _ in range(8)]
            packet = EEGChunk(timestamps=[random.random()], data=[sample])
            payload = {
                "type": "EEG_DATA",
                "timestamps": packet.timestamps,
                "data": packet.data
            }
            websocket.send_json(payload)
            await asyncio.sleep(0.1)  # Adjust sleep for real-time simulation


# @pytest.mark.skip # Skip this test for now
@pytest.mark.asyncio
async def test_bci_session(testapp):  # Use the 'testapp' fixture
    session_id = SESSION_ID
    with testapp.websocket_connect("api/v1/bci/stream/"+session_id) as websocket:
        # Send handshake packet (START)
        websocket.send_json({
            "type": "START",
            "session_id": session_id,
            "sampling_rate": "200",  # Adjust for your sampling rate
            "channel_labels": ['T3', 'T4', 'C3', 'C4', 'O1', 'O2', 'P3', 'P4']
        })
        # read ack
        channel_labels = websocket.receive_text()
        ack = websocket.receive_text()
        print(ack)
        assert "ACK" in ack
        # Create an asyncio task to send data asynchronously
        send_task = asyncio.create_task(send_fake_data(websocket))
        # wait for some data to be sent
        await asyncio.sleep(1)
        # Check if the session is created while data is being sent
        response = testapp.get("api/v1/bci/sessions")
        assert response.status_code == 200

        # Check if session exists in the response
        sessions = response.json()  # The response is directly a list of sessions

        found_session = any(session["session_id"] ==
                            session_id for session in sessions)
        assert found_session, "Session not found"


        # Add more assertions to verify the correctness of the data received and processed by your application.

        # keep the session open for a while and sending data
        await asyncio.sleep(2)
        # stop sending data before cancelling
        send_task.cancel()
        # Send end packet
        websocket.send_json({
            "type": "END",
            "session_id": session_id
        })
        # check end response, get the last text message


        # keep accumulating text until the last response is received
        end_response_accumulator = []
        while True:
            try:
                end_response_accumulator.append(websocket.receive_text())
            except:
                break
        print(end_response_accumulator)
        assert "Session ended" in end_response_accumulator[-1]


# # 1. Data Consistency Tests
# @pytest.mark.asyncio
# async def test_duplicate_timestamp(testapp):
#     session_id = "test_duplicate_timestamp"
#     with testapp.websocket_connect(f"api/v1/bci/stream/{session_id}") as websocket:
#         await websocket.send_json({
#             "type": "START",
#             "session_id": session_id,
#             "sampling_rate": 200,
#             "channel_labels": ['T3', 'T4', 'C3', 'C4', 'O1', 'O2', 'P3', 'P4']
#         })
#         # Send duplicate timestamp
#         for _ in range(2):
#             packet = EEGChunk(timestamps=[1.0], data=[
#                               [random.random() for _ in range(8)]])
#             await websocket.send_json({
#                 "type": "EEG_DATA",
#                 "timestamps": packet.timestamps,
#                 "data": packet.data
#             })
#             await asyncio.sleep(0.1)
#         await websocket.send_json({"type": "END", "session_id": session_id})
#         response = await websocket.receive_json()
#         # Assert for a specific error message or behavior related to duplicate timestamps
#         assert "Error: Duplicate timestamp" in response.get(
#             "error", ""), response


@pytest.mark.asyncio
async def test_inconsistent_timestamp(testapp):
    # ... Similar structure to test_duplicate_timestamp, but send timestamps that are not consistent with the sampling rate ...
    pass

# 2. Data Processing Test


# @pytest.mark.asyncio
# async def test_data_processing_summary(testapp):
#     expected_calibration_samples = 1000  # Adjust based on the expected number of samples
#     session_id = "test_data_processing_summary"
#     # ... Send real EEG data from a file or known source ...
#     # ... After session ends, fetch session statistics ...
#     response = testapp.get(f"api/v1/bci/sessions/{session_id}")
#     assert response.status_code == 200
#     session_stats = response.json()

#     # Assert the correctness of the summary statistics (e.g., number of samples, duration)
#     assert session_stats["calibration_data"] == expected_calibration_samples
#     # ... add more assertions for other statistics ...

# # 3. Session State Management Tests


@pytest.mark.asyncio
async def test_invalid_state_transitions(testapp):
    # ... Test cases to check for errors or proper handling when attempting invalid state transitions (e.g., starting classification before calibration) ...
    pass

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


# TODO:  Extra streaming tests
# 1. data consistency test
# what if i send the same timestamp twice
# what if the timestamp is not consistent with sampling rate
# what if the data is not consistent with the channel labels

# 2. data processing test
# use measured test data and check if the summary of the session is correct
# what if the session is closed without any data

# 3. session state management test
# what if i start calibration while the session is already in classification mode
# what if i start classification while the session is already in calibration mode
# what if i start classification without training the model
# what if i start classification without calibration
# what if i start classification without any data
# what if i start classification without any channel labels
