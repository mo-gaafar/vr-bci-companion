from dataclasses import dataclass, field
from .models import EEGData, EEGMode, EEGMarker, CueType, EEGChunk, EEGSpecification
from .models import EEGData, EEGMode, EEGMarker, CueType
from typing import Optional
from enum import Enum, auto
import uuid


class SessionState(Enum):
    CALIBRATION = auto()
    TRAINING = auto()
    CLASSIFICATION = auto()


@dataclass
class BCISession:
    # Fields without default values first
    session_id: uuid.UUID = field(default_factory=uuid.uuid4)
    calibration: Optional[EEGData] = None
    classification: Optional[EEGData] = None
    specifications: Optional[EEGSpecification] = None

    # Fields with default values next
    state: SessionState = SessionState.CALIBRATION
    eeg_data: list[EEGChunk] = field(default_factory=list)
    classification_model: Optional[object] = None

    def init_calibration(self):
        """Initialize the calibration data object."""
        self.calibration = EEGData(
            session_id=self.session_id, mode=EEGMode.CALIBRATION, data=[], timestamps=[], sampling_rate=0)
        # set calibration mode
        self.set_state(SessionState.CALIBRATION)

    def end_calibration(self):
        """End the calibration session."""
        self.set_state(SessionState.TRAINING)

    def init_classification(self):
        # stop calibration
        self.set_state(SessionState.TRAINING)
        # check if calibration data is available
        calibration_data = self.get_calibration_data()
        if calibration_data is None:
            raise Exception("Calibration data is not available.")
        # train the model
        self.classification_model = train_model(calibration_data)

        # start classification
        self.classification = EEGData(
            session_id=self.session_id, mode=EEGMode.CLASSIFICATION, data=[], timestamps=[], sampling_rate=0)
        self.set_state(SessionState.CLASSIFICATION)

    def get_calibration_data(self):
        # more complex data handling logic can be added here
        # for example if the calibration data is not available, it can return an error message
        # but first it may check if the calibration data is available in the datalake
        return self.calibration

    def get_calibraiton_model(self):
        # look for model in the datalake, the model will be stored as a pickle file
        # start by checking locally in the temp folder and then
        # check in the datalake if the model is not found locally

        return self.classification_model

    def train_model(self):
        # implement the training logic here after the calibration data is available
        # and the session state is set to training
        # the model will be stored in the datalake as a pickle file
        pass

    def add_eeg_data(self, data: EEGChunk):
        """Add EEG data to the session. This will keep getting called as long as the session is active."""
        self.eeg_data.append(data)
        # Depending on the current state, handle the data differently
        if self.state == SessionState.CALIBRATION:
            self.handle_calibration(data)
        elif self.state == SessionState.TRAINING:
            self.handle_training(data)
            # this shouldnt do anything to the data, it should just
            # keep waiting for the training to finish and then change the state to classification
        elif self.state == SessionState.CLASSIFICATION:
            self.handle_classification(data)

    def add_channel_labels(self, channel_labels):
        """Add channel labels to the session."""

        # Implement logic to add channel labels
        pass

    def handle_calibration(self, data):
        """Handle calibration data."""
        # flatten the chunk and for each timestamp add a sample array and append it to the data
        for i, timestamp in enumerate(data.timestamp):
            sample = [data.data[j][i] for j in range(len(data.data))]
            self.calibration.data.append(sample)
            self.calibration.timestamps.append(timestamp)
        # Implement calibration logic here
        pass

    def output_session_summary(self):
        print(f"Session ID: {self.session_id}")
        print(f"Session state: {self.state}")
        # print(f"EEG data length: {len(self.eeg_data)}")
        print(f"Calibration data length: {len(self.calibration.data)} samples")
        print(
            f"Classification data length: {len(self.classification.data)} samples")

    def handle_training(self, data):
        """Handle training data."""
        # Implement model training logic here
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


class SessionManager:
    def __init__(self):
        self.sessions = {}

    def create_session(self, session_id) -> uuid.UUID:
        """Create a new BCI session and return its ID."""
        new_session = BCISession(session_id=session_id)
        self.sessions[new_session.session_id] = new_session
        return new_session.session_id

    def get_session(self, session_id: uuid.UUID) -> Optional[BCISession]:
        """Retrieve an existing BCI session by its ID."""
        return self.sessions.get(session_id)

    def end_session(self, session_id: uuid.UUID, normal_closure: bool = True):
        """End a session and return the session object."""
        # session = self.sessions.pop(session_id)
        session = self.get_session(session_id)
        # TODO: add session closing here
        print(f"Session {session_id} ended.")
        # print some session stats
        print(f"Session data length: {len(session.eeg_data)}")
        print(f"Session state: {session.state}")
        if len(session.calibration.timestamps) > 0:
            print(
                f"Session time range (Calibration): {session.calibration.timestamps[0]} - {session.calibration.timestamps[-1]}")
        return session


# Global session manager instance
session_manager = SessionManager()
