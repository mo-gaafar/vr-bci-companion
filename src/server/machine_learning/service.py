from .repo import MLRepo, S3MLRepo, LocalMLRepo
from .models import StorageType, TrainingStatus
# from tensorflow.keras.models import load_model
import pickle as pkl

from server.config import CONFIG
from typing import Dict, Optional
from typing import Tuple

from latss import LATSS


class MachineLearningService:
    def __init__(self):
        self.model_queue: list = []  # Queue for pending training tasks
        # Dictionary to store models and their statuses
        self.models: Dict[str, Tuple[object, TrainingStatus]] = {}
        self.repo: MLRepo = (
            S3MLRepo() if CONFIG.ML_CONFIG.MODEL_STORAGE == StorageType.s3 else LocalMLRepo()
        )

    def train_model(self, session_id: str, calibration_data: object = None, calib_path: str = None):
        """
        Train the model with the calibration data and source data.

        This function is designed to be run as a background task.
        """
        self.models[session_id] = (
            None, TrainingStatus.PENDING)  # Initial status: PENDING
        # Add the model to the models dictionary with status PENDING
        try:
            # untrained_model = self.repo.load_untrained_model()
            if calib_path:
                # Load the calibration data from the repo
                self.repo._load_from_storage(calib_path)
            elif calibration_data is None:
                calibration_data = self.repo._load_from_storage(
                    "calibration_raw"+session_id+".pkl")

            source_data = self.repo._load_from_storage("source_np.pkl")
            # Update status: IN_PROGRESS
            self.models[session_id] = (
                None, TrainingStatus.IN_PROGRESS)
            untrained_model = LATSS(source_data)
            self.models[session_id] = (
                untrained_model, TrainingStatus.IN_PROGRESS)
            # Train the model
            trained_model = untrained_model.calibrate(calibration_data)
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
            # try loading from storage
            print(f"Loading model from storage for session {session_id}")
            model = self.repo.load_model(session_id)
            if model:
                self.models[session_id] = (model, TrainingStatus.COMPLETED)
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
        # Make predictions using the model
        predictions = model.predict(data)
        # Take last prediction if array
        if isinstance(predictions, list):
            predictions = predictions[-1]
        return predictions

    def add_to_queue(self, session_id: str, calibration_data: object = None, calib_path: str = None):
        """
        Add a model training task to the queue.
        """
        # Checking if the calibration data is available and loading it
        if calib_path:
            # Load calibration data from the repo
            calibration_data = self.repo._load_from_storage(calib_path)
        elif calibration_data is None:
            calibration_data = self.repo._load_from_storage(
                "calibration_raw"+session_id+".pkl")
        elif calibration_data:
            # Add the task to the queue
            pass
        else:
            # Raise an exception if the calibration data is missing
            raise ValueError("Calibration data is required")

        # Add the task to the queue
        self.model_queue.append((session_id, calibration_data))

        # TODO: make this a background async task in a real-world application
        while self.model_queue:
            session_id, calibration_data = self.model_queue.pop(0)
            self.train_model(session_id, calibration_data)

ml_service = MachineLearningService()
