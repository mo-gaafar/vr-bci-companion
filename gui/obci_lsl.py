from PyQt5.QtCore import QUrl
import uuid
import asyncio
import json
import pylsl
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWebSockets import QWebSocket

LOCAL_BASE_URL = "ws://localhost:8000/api/v1"
ONLINE_BASE_URL = "ws://server.neurohike.quest/api/v1"


class WebSocketHandler(QObject):
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    textMessageReceived = pyqtSignal(str)
    connectionAcknowledged = pyqtSignal()
    errorOccurred = pyqtSignal(str)  # Added for error reporting

    def __init__(self, session_id, channel_labels):
        super().__init__()
        self.session_id = session_id
        self.channel_labels = channel_labels
        self.websocket = QWebSocket()
        self.websocket.connected.connect(self.connected)
        self.websocket.disconnected.connect(self.disconnected)
        self.websocket.textMessageReceived.connect(
            self.on_text_message_recieved)

        # Connection status for reconnect attempts
        self.connected_successfully = False

    def connect(self, server_type="local"):
        base_url = LOCAL_BASE_URL if server_type == "local" else ONLINE_BASE_URL
        url = f"{base_url}/bci/stream/{self.session_id}"
        self.websocket.open(QUrl(url))

    async def send_initial_frame(self):
        initial_frame = {
            "type": "START",
            "session_id": self.session_id,
            "channel_labels": self.channel_labels,
            "sampling_rate": 250,
        }
        print("Sending initial frame")
        self.websocket.sendTextMessage(json.dumps(initial_frame))

    async def send_data(self, data):
        if self.websocket.isValid():
            print("Sending data")
            await self.websocket.sendTextMessage(json.dumps(data))

    def on_text_message_recieved(self, message):
        if message.startswith("ACK"):
            self.connected_successfully = True
            self.connectionAcknowledged.emit()
        else:
            self.textMessageReceived.emit(message)


async def lsl_stream_to_websocket(self, stream_config, server_type="local"):
    # Resolve the LSL stream

    # TODO: Change to use all streams? Or allow user to select stream
    name = stream_config["stream_1"]["name"]
    # send signal to update connection status
    self.connectionStatus.emit("Connecting to LSL stream...")
    streams = pylsl.resolve_byprop(
        "name", name, timeout=5.0)

    if not streams or len(streams) == 0:
        # raise ValueError(f"Could not find LSL stream: {name}")
        self.connectionStatus.emit(f"Could not find LSL stream: {name}")
        # reactivate the connect button
        self.connectButton.setEnabled(True)
        # unhide the server select combobox
        self.comboBox_server_select.setEnabled(True)

        return

    inlet = pylsl.StreamInlet(streams[0])

    session_id = uuid.uuid4().hex
    handler = WebSocketHandler(session_id, stream_config.get("channel_labels"))

    async def send_loop():
        chunk_size = 64
        samples_buffer = []
        timestamps_buffer = []
        send_queue = asyncio.Queue()  # Queue for sending chunks

        async def send_task():  # Separate task for sending chunks
            while True:
                chunk = await send_queue.get()
                if chunk is None:  # Sentinel value to stop the task
                    break
                await handler.send_data(chunk)

        asyncio.create_task(send_task())  # Start the sending task

        while True:
            if handler.connected_successfully:
                try:
                    sample, timestamp = inlet.pull_sample(timeout=1.0)

                    if sample:
                        samples_buffer.append(sample)
                        timestamps_buffer.append(timestamp)

                    # Send only when the buffer is full, or if there's data and the connection is lost
                    if (len(samples_buffer) >= chunk_size) or (samples_buffer and not handler.connected_successfully):
                        chunk_data = {
                            "data": samples_buffer,
                            "timestamps": timestamps_buffer
                        }
                        await send_queue.put(chunk_data)  # Put chunk in the queue
                        samples_buffer = []
                        timestamps_buffer = []

                except Exception as e:  # Error handling for LSL stream
                    print(f"Error pulling sample from LSL stream: {e}")
                    # Consider reconnecting or other error recovery actions here

            await asyncio.sleep(0.1)  # Control the rate of checking for data

        # Stop the sending task when the loop ends
        await send_queue.put(None)
    
    async def reconnect_loop():
        while True:
            await asyncio.sleep(5)
            if not handler.connected_successfully:
                handler.connect(server_type)  # Retry connecting
                await handler.send_initial_frame()

    # Create tasks for sending and reconnecting
    send_task = asyncio.create_task(send_loop())
    reconnect_task = asyncio.create_task(reconnect_loop())
    await asyncio.gather(send_task, reconnect_task)  # Run concurrently
