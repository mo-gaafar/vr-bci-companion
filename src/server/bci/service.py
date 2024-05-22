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
    session_id: uuid.UUID = field(default_factory=uuid.uuid4)
    state: SessionState = SessionState.CALIBRATION
    eeg_data: list[EEGChunk] = field(default_factory=list)
    classification_model: Optional[object] = None

    calibration: EEGData = field(default_factory=lambda: EEGData(
        mode=EEGMode.CALIBRATION,
        sampling_rate=0  # Set actual sampling rate when known
    ))

    classification: EEGData = field(default_factory=lambda: EEGData(
        mode=EEGMode.CLASSIFICATION,
        sampling_rate=0  # Set actual sampling rate when known
    ))

    specifications: EEGSpecification = field(default_factory=EEGSpecification)

    def add_eeg_data(self, data: EEGChunk):
        """Add EEG data to the session."""
        self.eeg_data.append(data)
        # Depending on the current state, handle the data differently
        if self.state == SessionState.CALIBRATION:
            self.handle_calibration(data)
        elif self.state == SessionState.TRAINING:
            self.handle_training(data)
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

    def handle_classification(self, data):
        """Handle classification (inference) data."""
        # Implement classification logic here
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
