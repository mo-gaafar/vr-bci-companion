import mne.io
from enum import Enum
from typing import Dict, Optional
from pydantic import BaseModel, Field


class ModelTrainingRequest(BaseModel):
    session_id: str = Field(
        ..., description="Session ID to fetch calibration data for model training")
    parameters: Optional[Dict[str, float]] = Field(
        None, description="Optional parameters for model training, e.g., learning rate")


class ModelTrainingResponse(BaseModel):
    message: str
    ml_model_id: str = Field(...,
                          description="A unique identifier for the trained model")


class ClassEnum(int, Enum):
    feet = 1
    rest = 0
    left = 2
    right = 3


class StorageType(str, Enum):
    local = "local"
    s3 = "s3"


class TrainingStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    NOT_FOUND = "NOT_FOUND"
    PENDING = "PENDING"
