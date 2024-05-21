import mne.io
from enum import Enum
from typing import Dict, Optional
from pydantic import BaseModel, Field


class ModelTrainingRequest(BaseModel):
    sessionId: str = Field(
        ..., description="Session ID to fetch calibration data for model training")
    parameters: Optional[Dict[str, float]] = Field(
        None, description="Optional parameters for model training, e.g., learning rate")


class ModelTrainingResponse(BaseModel):
    message: str
    modelId: str = Field(...,
                         description="A unique identifier for the trained model")


class ClassEnum(int, Enum):
    feet = 1
    rest = 0
    left = 2
    right = 3

# These models are to be recieved already serialized and everything,
# also note that the source domain dataset is too large to be retrieved multiple times so im thinking to save it somehow in the filesystem??...


class TrainedModel:
    def __init__(self):
        self.f_sample = 160  # Input Sampling frequency
        self.epoch_length = 1  # Length of each epoch in seconds
        self.overlap = 0.5

    def predict(self, input_data: mne.io.Raw) -> ClassEnum:
        # Perform prediction using the trained model
        predicted_class = ClassEnum.rest
        return predicted_class


class ModelCalibrator:
    def __init__(self):
        self.f_sample = 160  # Input Sampling frequency
        self.epoch_length = 1  # Length of each epoch in seconds
        self.overlap = 0.5  # Overlap ratio between epochs

    def calibrate(self, calibration_data: mne.io.Raw) -> TrainedModel:
        # Perform calibration using the provided data
        calibrated_model = {}
        return calibrated_model
