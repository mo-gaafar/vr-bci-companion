from server.machine_learning.models import TrainingStatus
import time
from server.machine_learning.service import ml_service
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
            self.session.end_calibration()
            self.session.init_training()
        elif new_state == SessionState.READY_FOR_CLASSIFICATION and old_state == SessionState.TRAINING:
            model_id = "placeholder"  # Get model ID from somewhere
            self.session.init_classification(model_id)
        elif new_state == SessionState.CLASSIFICATION and old_state == SessionState.READY_FOR_CLASSIFICATION:
            # Start classification (allow this transition)
            pass
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
        else:  # Ignore data in other states
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
    
    classification_buffer: List = field(default_factory=list)
    prediction_buffer: List = field(default_factory=list)

    storage_repo: Union[
        # InfluxDBTimeSeriesRepository,
        # MongoDbTimeSeriesRepository,
        LocalPickleStorage,
        S3PickleStorage,
    ] = field(default_factory=LocalPickleStorage)
    chunk_size_threshold: int = 1000


    calibration_raw: Optional[RawArray] = None
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
        try:
            # Transition to calibration state
            self.state_handler.transition_to(SessionState.CALIBRATION)
            return True
        except Exception as e:
            print(f"Error initializing calibration: {e}")
            return None

    def handle_calibration_data(self, data: EEGChunk):
        """Handles EEG data during calibration."""
        # Append data to the calibration buffer
        # self.eeg_buffer.append(data)
        # Append data to the calibration raw object
        # flatten the eeg chunk and append to calibration mne.io raw object
        # Check if we have enough data to end calibration  (based on calibration protocol total length)
        from .util import calc_protocol_time
        if self.calibration_raw >= calc_protocol_time(self.calibration_protocol):
            self.state_handler.transition_to(SessionState.TRAINING)
            print("Calibration complete. Starting training..")
        else:
            data = np.array(data.data).flatten()
            self.calibration_raw.append(data)
            print(f"Calibration data length: {len(self.calibration_raw)}")

    def end_calibration(self):
        """End the calibration process."""
        # Store calibration data
        self.storage_repo.save(self.calibration_raw,
                               "calibration_raw"+str(self.session_id))

        print("Calibration complete. Starting training..")
        self.state_handler.transition_to(SessionState.TRAINING)

    def init_training(self):
        """Initialize model training."""
        # Feed calibration data to the ML service and start training
        ml_service.add_to_queue(self.calibration_raw)

    def init_classification(self, model_id: str):
        """Initialize classification with the loaded model."""
        self.classification_model = ml_service.load_model(model_id)

    def handle_classification_data(self, data: EEGChunk):
        """Handles EEG data during classification, makes predictions, and processes results."""
        # Append data to the classification buffer
        self.classification_buffer.append(data)

    def get_classification_results(self):
        """Get the latest classification results."""
        pred = ml_service.classify(self.session_id, self.classification_buffer)
        # Add to prediction buffer
        self.prediction_buffer.append((time.time(), pred))
        return pred

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
