

from PyQt5 import QtCore
import pylsl
import time

""" obci_lsl.py - LSL streaming functions for NeuroRehab Connect"""
class LSLStreamingThread(QtCore.QThread):
    data_received = QtCore.pyqtSignal(str, float, list)  # Signal for data
    connection_status = QtCore.pyqtSignal(str)  # Signal for status updates

    def __init__(self, stream_config):
        super().__init__()
        self.stream_config = stream_config
        self.stop_streaming = False
        self.inlets = {}

    def run(self):
        self.connection_status.emit("Connecting")
        try:
            for stream_id, config in self.stream_config.items():
                streams = pylsl.resolve_stream('name', config['name'])

                if not streams:
                    self.connection_status.emit(
                        f"Stream '{config['name']}' not found.")
                    continue

                self.connection_status.emit(
                    f"Connected to stream: {stream_id}")
                self.inlets[stream_id] = pylsl.StreamInlet(streams[0])

            while not self.stop_streaming:
                for stream_id, inlet in self.inlets.items():
                    sample, timestamp = inlet.pull_sample(timeout=0.0)
                    if sample:
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
