import uuid
import pickle
from collections import deque
from typing import Optional, List, Union

import numpy as np
import mne
from mne.io import RawArray

from fastapi import WebSocket, WebSocketDisconnect

from server.machine_learning.service import MachineLearningService

from server.common.repo.pickle_storage import LocalPickleStorage, S3PickleStorage
# from server.common.repo.timeseries import (
#     # InfluxDBTimeSeriesRepository,
#     # MongoDbTimeSeriesRepository,
#     # store_eeg_data,
# )
from server.bci.models import (
    EEGChunk,
    SessionState,
    ConnectionStatus,
    EEGData,
    EEGMode,
)

from dataclasses import dataclass, field


@dataclass
class BCISession:
    """
    Represents a BCI (Brain-Computer Interface) session.

    Handles the collection, processing, and analysis of EEG data during calibration, training, and classification phases.
    """

    # Fields without default values
    session_id: uuid.UUID

    # Fields with default values
    state: SessionState = SessionState.UNSTARTED
    connection_status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    eeg_buffer: deque = field(default_factory=lambda: deque(maxlen=1000))
    last_received_timestamp: float = 0
    last_processed_timestamp: float = 0
    classification_model: Optional[object] = None
    classification_buffer: List = field(default_factory=list)
    storage_repo: Union[
        # InfluxDBTimeSeriesRepository,
        # MongoDbTimeSeriesRepository,
        LocalPickleStorage,
        S3PickleStorage,
    ] = field(default_factory=LocalPickleStorage)
    chunk_size_threshold: int = 1000
    calibration_data: Optional[RawArray] = None
    # events: Optional[List[list]] = None
    # event_id: Optional[dict] = None
    info: Optional[mne.Info] = None
    # raw: Optional[RawArray] = None

    def update_state(self, new_state: Optional[SessionState] = None):
        if new_state:
            self.state = new_state
        if self.state == SessionState.CALIBRATION:
            # enter once the calibration mode is started
            if self.last_state != SessionState.CALIBRATION:
                self.init_calibration()
        elif self.state == SessionState.TRAINING:
            # enter once the training mode is started
            if self.last_state != SessionState.TRAINING:
                self.init_training()

        self.last_state = self.state

    def add_eeg_data(self, data: EEGChunk):
        """Add EEG data to the session and process it based on the current state."""
        self.update_state()
        if self.state == SessionState.CLASSIFICATION or self.state == SessionState.CALIBRATION:
            for sample, timestamp in zip(data.data, data.timestamps):
                self.eeg_buffer.append((sample, timestamp))

            if len(self.eeg_buffer) >= self.chunk_size_threshold:
                self.process_buffer()

            self.handle_classification(data)

    def init_calibration(self):
        """Handle EEG data during calibration."""
        if not self.info:
            # Initialize MNE Info object if not already done
            self.info = mne.create_info(
                ch_names=self.channel_labels,
                sfreq=self.calibration_data.sampling_rate,
                ch_types=["eeg"] * len(self.channel_labels),
            )
            self.raw = mne.io.RawArray(
                np.zeros((len(self.channel_labels), 0)), info=self.info, verbose=False
            )

        if self.raw:
            new_data = np.array(self.calibration_data.data)
            self.raw.append(
                mne.io.RawArray(new_data, info=self.info, verbose=False)
            )

        if self.raw is not None and self.calibration_data is None and self.events is not None and self.event_id is not None:
            self.calibration_data = mne.Epochs(
                self.raw, events=self.events, event_id=self.event_id, tmin=-0.2, tmax=0.5
            )
        # ... rest of the method (store calibration data, check duration, etc.)
        #

    def process_buffer(self):
        """Process the data in the buffer."""
        while self.eeg_buffer:
            sample, timestamp = self.eeg_buffer.popleft()
            if self.state == SessionState.CALIBRATION:
                self.calibration_data.data.append(sample)
                self.calibration_data.timestamps.append(timestamp)
                self.last_received_timestamp = timestamp
            elif self.state in (SessionState.TRAINING, SessionState.CLASSIFICATION):
                # Convert sample to a NumPy array and reshape for MNE
                new_data = np.array(sample).reshape(1, -1)
                # Assuming session.raw is already initialized
                if self.raw is None:
                    self.raw = mne.io.RawArray(
                        new_data, info=self.info, verbose=False
                    )
                else:
                    self.raw.append(
                        mne.io.RawArray(
                            new_data, info=self.info, verbose=False)
                    )
                self.last_received_timestamp = timestamp

        # Determine storage type based on chunk size
        if len(self.calibration_data.data) >= self.chunk_size_threshold:
            self.storage_repo = LocalPickleStorage()  # Switch to LocalPickleStorage
        else:
            # self.storage_repo = MongoDbTimeSeriesRepository()  # Switch to time-series
            raise NotImplementedError("Timeseries storage not implemented yet.")

        # Store the data in the chosen repository
        self.storage_repo.store_data(self.calibration_data)

    def output_session_summary(self):
        print(f"Session ID: {self.session_id}")
        print(f"Session state: {self.state}")
        # print(f"EEG data length: {len(self.eeg_data)}")
        print(
            f"Calibration data length: {len(self.calibration_data.data)} samples")
        print(
            f"Classification data length: {len(self.calibration_data.data)} samples")

    def init_training(self):
        """Starts the training mode."""
        # Implement model training status checker here
        # if status is done then change the state to classification

        pass

    def handle_classification(self, data: EEGChunk):
        epoch_length = 100  # Adjust for your sampling rate and desired epoch length
        epoch_overlap = 50  # 50% overlap
        # Append new data to the buffer
        self.classification_buffer.extend(data.data)

        # While the buffer has enough data for a prediction...
        while len(self.classification_buffer) >= epoch_length:
            # Extract the current epoch
            epoch_data = self.classification_buffer[:epoch_length]

            # Make a prediction
            prediction = self.classification_model.predict(epoch_data)

            # Remove old data (adjust for overlap)
            self.classification_buffer = self.classification_buffer[epoch_overlap:]

            # ... Handle the prediction result ...
            pass

    def set_state(self, new_state: SessionState):
        """Set the session state."""
        self.state = new_state

    def get_session_stats(self):
        try:
            calibration_data_len = len(
                self.calibration_data.data) if self.calibration_data else 0
            classification_data_len = len(
                self.classification_buffer) if self.classification_buffer else 0
            eeg_buffer_len = len(self.eeg_buffer) if self.eeg_buffer else 0
            dict_out =  {
                "session_id": self.session_id,
                "state": str(self.state),
                "channels": dict(self.info.ch_names if self.info else None),
                "calibration_data": calibration_data_len,
                "classification_data": classification_data_len,
                "eeg_buffer_data": eeg_buffer_len
            }
            return dict_out
        except Exception as e:
            print(f"Error getting session stats: {e}")
            return None

    def __dict__(self):
        return {
            "session_id": self.session_id,
            "state": str(self.state),
            "channels": dict(self.info.ch_names if self.info else None),
        }


class SessionManager:
    def __init__(self):
        self.sessions = []

    def create_session(self, session_id) -> uuid.UUID:
        """Create a new BCI session and return its ID."""
        new_session = BCISession(session_id=session_id)
        # check if session already exists in memory
        if session_id in self.sessions:
            raise Exception("Session already exists.")
        self.sessions.append(new_session)
        return new_session

    def get_session(self, session_id: uuid.UUID) -> Optional[BCISession]:
        """Retrieve an existing BCI session by its ID."""
        for session in self.sessions:
            if str(session.session_id) == str(session_id):
                return session
        return None

    def end_session(self, session_id: uuid.UUID, normal_closure: bool = True):
        """End a session and return the session object."""
        # session = self.sessions.pop(session_id)
        session = self.get_session(session_id)
        # TODO: add session closing here
        print(f"Session {session_id} ended.")
        # print session stats dict
        print(session.get_session_stats())
        return session


# Global session manager instance
session_manager = SessionManager()
