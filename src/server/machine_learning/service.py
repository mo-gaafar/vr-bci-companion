from .repo import MLRepo, S3MLRepo, LocalMLRepo
from .models import StorageType, TrainingStatus
# from tensorflow.keras.models import load_model
import pickle as pkl

from server.config import CONFIG
from typing import Dict, Optional
from typing import Tuple


class MachineLearningService:
    def __init__(self):
        self.model_queue: list = []  # Queue for pending training tasks
        # Dictionary to store models and their statuses
        self.models: Dict[str, Tuple[object, TrainingStatus]] = {}
        self.repo: MLRepo = (
            S3MLRepo() if CONFIG.ML_CONFIG.MODEL_STORAGE == StorageType.s3 else LocalMLRepo()
        )

    async def train_model(self, session_id: str, calibration_data: object):
        """
        Train the model with the calibration data and source data.
        
        This function is designed to be run as a background task.
        """
        self.models[session_id] = (
            None, TrainingStatus.PENDING)  # Initial status: PENDING
        try:
            untrained_model = self.repo.load_untrained_model()
            source_data = self.repo._load_from_storage("source_data.pkl")
            # Update status: IN_PROGRESS
            self.models[session_id] = (
                untrained_model, TrainingStatus.IN_PROGRESS)
            trained_model = untrained_model.fit(
                source_data, calibration_data)  # Train the model
            # Update status: COMPLETED
            self.models[session_id] = (trained_model, TrainingStatus.COMPLETED)
            self.repo.store_model(trained_model, session_id)
        except Exception as e:
            self.models[session_id] = (None, TrainingStatus.FAILED)
            print(f"Error during model training: {e}")
            raise  # Re-raise the exception so it can be handled elsewhere

    def get_model_status(self, session_id: str) -> TrainingStatus:
        """Get the training status of a model."""
        _, status = self.models.get(
            session_id, (None, TrainingStatus.NOT_FOUND))
        return status

    def load_model(self, session_id: str) -> Optional[object]:
        """Load the trained model for classification, if available."""
        model, status = self.models.get(session_id, (None, None))
        if status == TrainingStatus.COMPLETED:
            return model
        else:
            print(
                f"Cannot load model for session {session_id}: Status is {status}")
            return None  # Or raise an exception, depending on your error handling strategy

    def classify(self, session_id: str, data: object):
        """Classify the data using the trained model for the given session."""
        model = self.load_model(session_id)
        if model is None:
            raise ValueError(
                f"Model not loaded or training not completed for session {session_id}"
            )
        return model.predict(data)

    async def add_to_queue(self, session_id: str, calibration_data: object):
        """
        Add a model training task to the queue.
        """
        self.model_queue.append((session_id, calibration_data))

        # Process the queue in the background
        while self.model_queue:
            session_id, data = self.model_queue.pop(0)
            await self.train_model(session_id, data)


ml_service = MachineLearningService()
