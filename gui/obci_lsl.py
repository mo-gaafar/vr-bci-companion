from PyQt5.QtWebSockets import QWebSocket
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QUrl, QTimer
from PyQt5.QtCore import QUrl, pyqtSignal, QThread, QTimer
import uuid
import pylsl
import json
import time
from PyQt5.QtNetwork import QAbstractSocket

# Now you can safely set up your signals and slots that use SocketState



BASE_WS_URL = "ws://localhost:8000/api/v1"


class WebSocketWorker(QObject):
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    textMessageReceived = pyqtSignal(str)
    connectionAcknowledged = pyqtSignal(bool)

    def __init__(self, session_id, channel_labels):
        super().__init__()
        self.session_id = session_id
        self.channel_labels = channel_labels
        self.websocket = QWebSocket()
        self.websocket.connected.connect(self.connected)
        self.websocket.disconnected.connect(self.disconnected)
        self.websocket.textMessageReceived.connect(
            self.on_text_message_recieved)
        self.ack_timer = QTimer(self)
        self.ack_timer.setSingleShot(True)
        self.ack_timer.timeout.connect(self.handle_ack_timeout)

    def connect(self):
        url = f"{BASE_WS_URL}/bci/stream/{self.session_id}"
        self.websocket.open(QUrl(url))

    def send_initial_frame(self):
        initial_frame = {
            "type": "START",
            "session_id": self.session_id,
            "channel_labels": self.channel_labels
        }
        self.websocket.sendTextMessage(json.dumps(initial_frame))
        self.ack_timer.start(30000)

    def send_data(self, data):
        if self.websocket.isValid():
            self.websocket.sendTextMessage(json.dumps(data))

    def on_text_message_recieved(self, message):
        if message == "ACK":
            self.ack_timer.stop()
            self.connectionAcknowledged.emit(True)
        else:
            self.textMessageReceived.emit(message)

    def handle_ack_timeout(self):
        print("ACK not received, closing connection.")
        self.websocket.close()


class LSLStreamingThread(QThread):
    data_received = pyqtSignal(str, float, list)
    connectionStatus = pyqtSignal(str)

    def __init__(self, stream_config):
        super().__init__()
        self.stream_session_id = uuid.uuid4().hex
        self.stream_config = stream_config
        self.worker = WebSocketWorker(
            self.stream_session_id, self.stream_config.get('channel_labels'))
        # self.worker.moveToThread(self)
        self.worker.connectionAcknowledged.connect(self.start_streaming)
        self.worker.connected.connect(self.worker.send_initial_frame)
        self.worker.textMessageReceived.connect(self.handle_message)

    def run(self):
        self.worker.connect()
        self.setup_streams()

    def setup_streams(self):
        for stream_id, config in self.stream_config.items():
            try:
                streams = pylsl.resolve_stream('name', config['name'])
                self.connectionStatus.emit(f"Connected to stream: {stream_id}")
                inlet = pylsl.StreamInlet(streams[0])
                while self.isRunning():
                    sample, timestamp = inlet.pull_sample(timeout=1.0)
                    if sample:
                        self.worker.send_data(
                            {"data": sample, "timestamp": timestamp})
                        self.data_received.emit(stream_id, timestamp, sample)
            except pylsl.LostError:
                self.connectionStatus.emit(f"Stream '{config['name']}' lost.")
            except Exception as e:
                self.connectionStatus.emit(str(e))

    def handle_message(self, message):
        print(f"Message from server: {message}")

    def start_streaming(self):
        self.connectionStatus.emit("Streaming...")

    def stop(self):
        self.stop_streaming = True
        # self.websocket_client.close_connection()
        print("Thread stopping and closing connection")  # Debug print


def start_lsl_connection(self, stream_config):
    if self.lsl_thread is None:
        self.lsl_thread = LSLStreamingThread(stream_config)
        self.lsl_thread.data_received.connect(self.handle_lsl_data)
        self.lsl_thread.connectionStatus.connect(
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
