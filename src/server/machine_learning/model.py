# These models are to be recieved already serialized and everything,
# also note that the source domain dataset is too large to be retrieved multiple times so im thinking to save it somehow in the filesystem??...
import mne.io
from typing import Dict, Optional
from pydantic import BaseModel, Field
from server.machine_learning.models import ClassEnum

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
