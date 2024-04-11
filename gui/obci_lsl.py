

from PyQt5 import QtCore
import pylsl
import time
import uuid
import websockets
import asyncio
import json

""" obci_lsl.py - LSL streaming functions for NeuroRehab Connect"""
BASE_WS_URL = "ws://localhost:8000"



class BackendWebsocketClient:
    '''Interface between the LSL thread and the backend server for streaming EEG data.'''

    def __init__(self, session_id, channel_labels=None):
        self.session_id = session_id
        self.channel_labels = channel_labels or [
            'T3', 'T4', 'C3', 'C4', 'O1', 'O2', 'P3', 'P4']
        self.websocket_url = f"{BASE_WS_URL}/bci/stream/{self.session_id}"
        self.websocket = None
        asyncio.run(self.setup_websocket())

    async def setup_websocket(self):
        '''Setup a persistent websocket connection to the backend server.'''
        try:
            self.websocket = await websockets.connect(self.websocket_url)
            await self.send_initial_frame()
        except Exception as e:
            print(f"Failed to connect to WebSocket server: {e}")

    async def send_initial_frame(self):
        '''Send initial data frame with session ID and channel labels.'''
        initial_frame = {
            "type": "START",
            "session_id": self.session_id,
            "channel_labels": self.channel_labels
        }
        await self.websocket.send(json.dumps(initial_frame))

    async def send_data(self, data):
        '''Send EEG data to the backend server over an open websocket connection.'''
        if self.websocket is None or self.websocket.closed:
            await self.setup_websocket()  # Attempt to reconnect if not connected
        try:
            await self.websocket.send(json.dumps(data))
        except Exception as e:
            print(f"Error sending data: {e}")

    def close_connection(self):
        '''Close the websocket connection.'''
        if self.websocket:
            asyncio.run(self.websocket.close())

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.websocket.close()


class LSLStreamingThread(QtCore.QThread):
    data_received = QtCore.pyqtSignal(str, float, list)  # Signal for data
    connection_status = QtCore.pyqtSignal(str)  # Signal for status updates

    def __init__(self, stream_config):
        super().__init__()
        self.stream_session_id = uuid.uuid4().hex
        self.stream_config = stream_config
        self.stop_streaming = False
        self.inlets = {}

        self.websocket_client = None

    def run(self):
        self.connection_status.emit("Connecting")
        try:
            for stream_id, config in self.stream_config.items():
                streams = pylsl.resolve_stream('name', config['name'])

                if not streams:
                    self.connection_status.emit(
                        f"Stream '{config['name']}' not found.")
                    continue

                # update the connection status in gui
                self.connection_status.emit(
                    f"Connected to stream: {stream_id}")

                # Initialize the LSL stream inlet (OpenBCI Cyton board)
                self.inlets[stream_id] = pylsl.StreamInlet(streams[0])

                # Initialize connection with the backend websocket to broadcast data to it
                self.websocket_client = BackendWebsocketClient(
                    self.stream_session_id, config.get('channel_labels'))

            while not self.stop_streaming:
                for stream_id, inlet in self.inlets.items():
                    sample, timestamp = inlet.pull_sample(timeout=0.0)
                    if sample:
                        # Send data to the backend server via websocket
                        print(sample, timestamp)
                        self.websocket_client.send_data(
                            {"data": sample, "timestamp": timestamp})

                        # Emit the data to the GUI
                        self.data_received.emit(stream_id, timestamp, sample)

                time.sleep(0.01)
        finally:
            self.connection_status.emit("Disconnected")

    def stop(self):
        self.stop_streaming = True


def start_lsl_connection(self, stream_config):
    if self.lsl_thread is None:
        self.lsl_thread = LSLStreamingThread(stream_config)
        self.lsl_thread.data_received.connect(self.handle_lsl_data)
        self.lsl_thread.connection_status.connect(
            self.update_connection_status)
        self.lsl_thread.start()


def stop_lsl_connection(self):
    if self.lsl_thread is not None:
        self.lsl_thread.stop()
        self.lsl_thread.wait()  # Wait for thread to finish
        self.lsl_thread = None


def update_connection_status(self, status):
    # Update your GUI's connection status display
    pass
