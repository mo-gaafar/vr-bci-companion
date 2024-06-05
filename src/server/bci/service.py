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

from server.bci.models import CalibrationProtocol
from .util import *


# State Machine Design
class SessionStateHandler:
    """Handles the state machine logic for a BCI session."""

    def __init__(self, session: 'BCISession'):
        self.session = session
        self.state = SessionState.UNSTARTED

    def transition_to(self, new_state: SessionState):
        """Handles state transitions and any associated actions."""
        old_state = self.state
        self.state = new_state

        if new_state == SessionState.CALIBRATION and old_state == SessionState.UNSTARTED:
            self.session.init_calibration(
                self.session.calibration_protocol)  # Pass protocol here
        elif new_state == SessionState.TRAINING and old_state == SessionState.CALIBRATION:
            self.session.init_training()
        elif new_state == SessionState.CLASSIFICATION and old_state == SessionState.TRAINING:
            model_id = "placeholder" # Get model ID from somewhere
            self.session.init_classification(model_id)
        elif new_state == SessionState.UNSTARTED:
            # Reset session state
            # self.session.state = SessionState.UNSTARTED
            self.session.connection_status = ConnectionStatus.DISCONNECTED
            self.session.eeg_buffer.clear()
            self.session.last_received_timestamp = 0
            self.session.last_processed_timestamp = 0
        else:
            raise ValueError(
                f"Invalid state transition from {old_state} to {new_state}")

    def handle_data(self, data: EEGChunk):
        """Delegates data handling to the appropriate method based on the current state."""
        if self.state == SessionState.CALIBRATION:
            self.session.handle_calibration_data(data)
        elif self.state == SessionState.CLASSIFICATION:
            self.session.handle_classification_data(data)
        else: # Ignore data in other states
            pass



@dataclass
class BCISession:
    """
    Represents a BCI (Brain-Computer Interface) session.

    Handles the collection, processing, and analysis of EEG data during calibration, training, and classification phases.
    """

    # Fields without default values
    session_id: uuid.UUID

    # Fields with default values
    # state: SessionState = SessionState.UNSTARTED
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
    calibration_protocol: Optional[CalibrationProtocol] = None
    calibration_events: Optional[List] = None
    calibration_duration: Optional[float] = None  # in seconds
    info: Optional[mne.Info] = None
    event_id: Optional[dict] = None

    # raw: Optional[RawArray] = None
    state_handler: SessionStateHandler = field(init=False)

    def __post_init__(self):
        """Initialization after dataclass fields are set."""
        self.state_handler = SessionStateHandler(self)

    def add_eeg_data(self, data: EEGChunk):
        """Entry point for new EEG data. Delegates to state handler."""
        self.state_handler.handle_data(data)

    def init_calibration(self, protocol: CalibrationProtocol):
        """Initialize calibration process."""
        # Setting up the raw and info and events 
        
        # Transition to calibration state
        self.state_handler.transition_to(SessionState.CALIBRATION)

    def handle_calibration_data(self, data: EEGChunk):
        """Handles EEG data during calibration."""
        # ... Your existing logic for appending data and checking for end of calibration ...

        # If calibration is complete, transition to training
        if self.raw.times[-1] - self.raw.times[0] >= self.calibration_duration:
            self.end_calibration()

    def end_calibration(self):
        # Create Epochs object from raw data and events
        self.calibration_data = mne.Epochs(
            self.raw, events=self.calibration_events, event_id=self.event_id, tmin=-0.2, tmax=0.5
        )
        # Store calibration data
        self.storage_repo.store_data(self.calibration_data)
        print("Calibration complete. Starting training..")
        self.state_handler.transition_to(SessionState.TRAINING)


    def init_training(self):
        """Initialize model training."""
        from server.machine_learning.service import ml_service
        # Add calibration data to the training queue
        # ml_service.
    def init_classification(self, model_id: str):
        """Initialize classification with the loaded model."""
        # ... (Load your model) ...
        self.state_handler.transition_to(SessionState.CLASSIFICATION)

    def handle_classification_data(self, data: EEGChunk):
        """Handles EEG data during classification, makes predictions, and processes results."""
        # ... Your existing logic for appending data, extracting epochs, making predictions, etc. ...

        """Set the session state."""
        self.state = new_state

    def get_session_stats(self):
        try:
            calibration_data_len = len(
                self.calibration_data.data) if self.calibration_data else 0
            classification_data_len = len(
                self.classification_buffer) if self.classification_buffer else 0
            eeg_buffer_len = len(self.eeg_buffer) if self.eeg_buffer else 0
            dict_out = {
                "session_id": self.session_id,
                "state": str(self.state_handler.state),
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
            "state": str(self.state_handler.state),
            "channels": dict(self.info.ch_names if self.info else None),
        }

# from .repo import ISessionRepository, session_repo


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
