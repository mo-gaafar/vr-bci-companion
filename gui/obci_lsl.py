from PyQt5.QtCore import QUrl
from PyQt5.QtWebSockets import QWebSocket
import asyncio
from PyQt5 import QtCore
import uuid
import pylsl
import websockets
import json
import time

BASE_WS_URL = "ws://localhost:8000/api/v1"


class WebsocketClient:
    '''Interface between the LSL thread and the backend server for streaming EEG data.'''

    def __init__(self, session_id, channel_labels=None):
        self.session_id = session_id
        self.channel_labels = channel_labels or [
            'T3', 'T4', 'C3', 'C4', 'O1', 'O2', 'P3', 'P4']
        self.websocket_url = f"ws://localhost:8000/api/v1/bci/stream/{self.session_id}"
        self.websocket = QWebSocket()
        self.websocket.connected.connect(self.on_connected)
        self.websocket.disconnected.connect(self.on_disconnected)
        self.websocket.textMessageReceived.connect(self.on_text_received)

        self.start_ack_received = False
        self.connect_to_websocket()

    def connect_to_websocket(self):
        '''Establish a WebSocket connection.'''
        self.websocket.open(QUrl(self.websocket_url))

    def on_connected(self):
        '''Handle WebSocket connection established.'''
        print("WebSocket connected")
        self.send_initial_frame()

    def send_initial_frame(self):
        '''Send initial data frame with session ID and channel labels.'''
        initial_frame = {
            "type": "START",
            "session_id": self.session_id,
            "channel_labels": self.channel_labels
        }
        self.websocket.sendTextMessage(json.dumps(initial_frame))

        print("Waiting for ACK, Timeout: 30s")
        self.ack_timer = QtCore.QTimer()
        self.ack_timer.setSingleShot(True)  # Timer will fire only once
        self.ack_timer.timeout.connect(self.handle_ack_timeout)
        self.websocket.textMessageReceived.connect(self.handle_ack_message)
        self.ack_timer.start(30000)  # 30 second timeout

    def handle_ack_message(self, message):
        if message == "ACK":
            print("ACK Received")
            self.start_ack_received = True
            self.ack_timer.stop()

    def handle_ack_timeout(self):
        print("ACK not received. Closing connection.")
        self.websocket.close()

    def send_data(self, data):
        '''Send EEG data to the backend server over an open websocket connection.'''
        if self.websocket.state() != QWebSocket.open:
            print("WebSocket not open. Cannot send data.")
            # try to reconnect
            self.connect_to_websocket()
            return
        print("WS Sending data:", data)
        self.websocket.sendTextMessage(json.dumps(data))
        # check if the socket is still open
        

    def get_start_ack(self):
        return self.start_ack_received

    def on_disconnected(self):
        '''Handle WebSocket disconnection.'''
        print("WebSocket disconnected")

    def on_text_received(self, message):
        '''Handle text messages received via WebSocket.'''
        print("Received message:", message)

    def close_connection(self):
        '''Close the websocket connection.'''
        self.websocket.close()


class LSLStreamingThread(QtCore.QThread):
    data_received = QtCore.pyqtSignal(str, float, list)
    connection_status = QtCore.pyqtSignal(str)

    def __init__(self, stream_config):
        super().__init__()
        self.stream_session_id = uuid.uuid4().hex
        self.stream_config = stream_config
        self.stop_streaming = False
        self.inlets = {}
        self.websocket_client = WebsocketClient(
            self.stream_session_id, self.stream_config.get('channel_labels'))

    def run(self):
        print("Starting LSL thread")
        self.connection_status.emit("Connecting")
        try:
            for stream_id, config in self.stream_config.items():
                print("entered loop")
                if not stream_id == "stream_1": # TODO: Remove this line later on
                    continue
                streams = pylsl.resolve_stream('name', config['name'])
                if not streams:
                    print("Stream not found")
                    self.connection_status.emit(
                        f"Stream '{config['name']}' not found.")
                    continue
                self.connection_status.emit(
                    f"Connected to stream: {stream_id}")
                self.inlets[stream_id] = pylsl.StreamInlet(streams[0])
            # while loop will run until stop_streaming is set to True and will not run if websocket start acknowledgement is not received
            # blocking loop so the thread will not exit until the connection is closed
            print("stop_streaming", self.stop_streaming)
            print("start_ack", self.websocket_client.get_start_ack())
            while not self.stop_streaming and not self.websocket_client.get_start_ack():
                time.sleep(5)
                print("Waiting for ACK")
            # streaming loop
            while not self.stop_streaming:
                for stream_id, inlet in self.inlets.items():
                    sample, timestamp = inlet.pull_sample(timeout=0.0)
                    if sample:
                        self.websocket_client.send_data(
                            {"data": sample, "timestamp": timestamp})
                        self.data_received.emit(stream_id, timestamp, sample)
                time.sleep(0.01)
        finally:
            self.websocket_client.close_connection()
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
