
'''
    Made for BCI models, note that our model has a label alignment stage
    which is not present in the typical machine learning pipeline so we 
    need to get source and target data separately and align them before
    training the model.

    Also note that the model is trained on the calibration data and then
    used to classify the classification data.

    The untrained model object is stored in the repository and then loaded
    and trained when the session is set to training mode.

    The trained model is then stored in the repository and loaded when the
    session is set to classification mode.

    Data format is MNE RawArray object.

    The repository should also handle the storage of the model and the data.
    Note that the first time the model is trained on calibration it takes a large portion of data and the 
    stored model is used to classify the data in the classification mode in real-time chunks based on the epoch length, overlap and fsample defined 
    in the imported model at the very beginning of the session.



    '''

from .models import StorageType
from server.common.repo.pickle_storage import LocalPickleStorage, S3PickleStorage
from datetime import datetime
from abc import ABC, abstractmethod
import pickle
from typing import Optional, Tuple

import mne
from mne.io import RawArray

import os
import pickle
from abc import ABC, abstractmethod
from typing import Optional, Tuple

import mne
from mne.io import RawArray
import numpy as np

from server.config import CONFIG

settings = CONFIG.ML_CONFIG



class MLRepo(ABC):
    """
    Abstract base class for Machine Learning model repositories in a BCI context.

    Handles model loading, training, and storage using either S3 or local pickle storage, depending on configuration.
    """

    def __init__(self, storage_type: str = settings.MODEL_STORAGE):
        self.storage_type = storage_type

    @abstractmethod
    def _load_from_storage(self, filename: str) -> Optional[object]:
        """Load an object (model or data) from the configured storage."""
        pass

    def get_file_path(self, filename: str, session_id: str = None) -> str:
        """Get the full file path for the given filename."""
        if session_id:
            return os.path.join(settings.MODELS_DIR, session_id, filename)
        return os.path.join(settings.MODELS_DIR, filename)

    def load_untrained_model(self) -> object:
        """Load an untrained model from S3 or local storage."""
        filename = settings.UNTRAINED_MODEL_FILE
        return self._load_from_storage(filename)

    # def train_model(
    #     self, model: object, X: np.ndarray, y: np.ndarray
    # ) -> object:
    #     """Train the model using the provided data and store it."""
    #     model.train(X, y)  # Call the model's train method directly
    #     metadata = {
    #         "model_type": model.__class__.__name__,
    #         "training_timestamp": datetime.now().isoformat(),  # Add more metadata as needed
    #     }
    #     self.store_model(model, metadata)
    #     return model

    @abstractmethod
    def _save_to_storage(self, obj: object, filename: str):
        """Save an object (model or data) to the configured storage."""
        pass

    def store_model(self, model: object, metadata: dict, filename: str = settings.TRAINED_MODEL_FILE, session_id: str = None):
        """Store the trained model and associated metadata to S3 or local storage."""
        with open(filename, "wb") as f:
            pickle.dump({"model": model, "metadata": metadata}, f)
        self._save_to_storage(filename)

    def load_model(self, session_id) -> object:
        """Load a trained model from S3 or local storage."""
        filename = settings.TRAINED_MODEL_FILE
        loaded_data = self._load_from_storage(filename)
        return loaded_data["model"] if loaded_data else None


class S3MLRepo(MLRepo):
    """MLRepo implementation using AWS S3."""

    def __init__(self):
        super().__init__(storage_type=StorageType.s3)
        self.storage = S3PickleStorage()

    def _load_from_storage(self, filename: str) -> Optional[object]:
        return self.storage.load(filename)

    def _save_to_storage(self, obj: object, filename: str):
        self.storage.save(obj, filename)


class LocalMLRepo(MLRepo):
    """MLRepo implementation using local file storage."""

    def __init__(self):
        super().__init__(storage_type=StorageType.local)
        self.storage = LocalPickleStorage()

    def _load_from_storage(self, filename: str) -> Optional[object]:
        return self.storage.load(filename)

    def _save_to_storage(self, obj: object, filename: str):
        self.storage.save(obj, filename)
