import logging
import threading
from collections import deque
from PyQt5 import QtCore
import time


class ConnectionStatus(QtCore.QObject):
    signal_quality_changed = QtCore.pyqtSignal(int)
    connection_status_changed = QtCore.pyqtSignal(str)


class ConnectionStrategy:  # Abstract Base Class
    def connect(self):
        raise NotImplementedError()

    def disconnect(self):
        raise NotImplementedError()


class SerialConnectionStrategy(ConnectionStrategy):
    # ... implementation for serial connection ...
    pass


class LSLConnectionStrategy(ConnectionStrategy):
    # ... implementation for LSL connection ...
    def connect(self):
        raise NotImplementedError

    def disconnect(self):
        raise NotImplementedError


class BCIStreamer:
    def __init__(self):
        self.port = None
        self.board = None
        self.is_connected = False
        self.signal_quality = 0
        self.data_buffer = deque(maxlen=100)
        logging.basicConfig(level=logging.INFO)
        self.autoconnect_enabled = False
        self._connect_thread = None
        self.connection_status = ConnectionStatus()
        self.connection_type = 'serial'  # Default to your existing method
        self.lsl_stream_names = ['obci_eeg1', 'obci_eeg2', 'obci_eeg3']
        self.inlets = []  # List for multiple inlets

    def connect(self):
        if self.connection_type == 'serial':
            self.strategy = SerialConnectionStrategy()
        elif self.connection_type == 'pylsl':
            self.strategy = LSLConnectionStrategy()
        else:
            raise ValueError("Invalid connection type")

        self.strategy.connect()  # Delegate to the strategy

    def _connect_loop(self):
        while True:
            if not self.is_connected:
                with self._port_mutex:  # Acquire the mutex
                    try:
                        self.board = Cyton('serial', self.port)
                        self.board.start_stream()
                        self.is_connected = True
                        self.connection_status.connection_status_changed.emit(
                            "Connected")

                    except Exception as e:
                        self.connection_status.connection_status_changed.emit(
                            "Connection Failed")
                        logging.error(f"Connection error: {str(e)}")
                        # Add error handling here if needed
                        time.sleep(1)

    def disconnect(self):
        if self.connection_type == 'serial':
            if self.board:
                self.board.stop_stream()
                self.is_connected = False
                self._connect_thread = None
        if self.connection_type == 'pylsl':
            for inlet in self.inlets:
                del inlet  # Close each inlet
            self.inlets = []
            self.is_connected = False

    def start_streaming(self, callback):
        self.connect()
        self.callback = callback
        if self.board:
            while self.is_connected:
                if self.connection_type == 'serial':
                    data_packet = self.get_data_packet()
                    self.callback(data_packet)
                    self.check_signal_quality(data_packet)
                if self.connection_type == 'pylsl':
                    for inlet in self.inlets:
                        sample, timestamp = inlet.pull_sample()
                        callback(sample)

    def stop_streaming(self):
        self.disconnect()

    def check_signal_quality(self, data_packet):
        self.data_buffer.append(data_packet.channels_data)
        self.signal_quality = self.calculate_signal_quality()
        self.connection_status.signal_quality_changed.emit(self.signal_quality)

    def calculate_signal_quality(self):
        # TODO: Your signal quality calculation logic here
        # Example (replace with your actual calculation):
        data_array = np.array(self.data_buffer)
        variances = np.var(data_array, axis=0)
        avg_variance = np.mean(variances)
        return avg_variance
