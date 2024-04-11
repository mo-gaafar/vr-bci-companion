from .models import EEGData, EEGMode, EEGMarker, CueType
from typing import Optional
from enum import Enum, auto
import uuid


class SessionState(Enum):
    CALIBRATION = auto()
    TRAINING = auto()
    CLASSIFICATION = auto()


class BCISession:
    def __init__(self, session_id=None):
        if session_id is None:
            self.session_id = uuid.uuid4()
        self.state = SessionState.CALIBRATION
        self.eeg_data = []  # This will store EEG data

        self.calibration = EEGData(
            session_id=str(self.session_id),
            mode=EEGMode.CALIBRATION,
            timestamp_epoch=None,
            channel_labels=[],
            data=[],
            sampling_rate=0,
            markers=[]
        )

        self.classification = EEGData(
            session_id=str(self.session_id),
            mode=EEGMode.CLASSIFICATION,
            timestamp_epoch=None,
            channel_labels=[],
            data=[],
            sampling_rate=0,
            markers=[]
        )

    def add_eeg_data(self, data):
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

        # Implement calibration logic here
        pass

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
    
    def end_session(self, session_id: uuid.UUID):
        """End a session and return the session object."""
        session = self.sessions.pop(session_id)
        print(f"Session {session_id} ended.")
        return session


# Global session manager instance
session_manager = SessionManager()
