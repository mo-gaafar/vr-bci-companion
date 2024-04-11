from datetime import datetime
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from enum import Enum


class LSLPacket(BaseModel):
    timestamp: float = Field(..., description="Timestamp of the LSL packet")
    data: List[float] = Field(...,
                              description="List of floating point values in the LSL packet")


class CueType(str, Enum):
    prepare = "Prepare"
    start_imagining_walking = "Start Imagining Walking"
    stop_and_rest = "Stop and Rest"
    repeat_or_end = "Repeat or End"


class EEGMode(Enum):
    CALIBRATION = "calibration"
    CLASSIFICATION = "classification"


class EEGMarker(BaseModel):
    name: str
    timestamp: datetime


class EEGData(BaseModel):
    session_id: str = Field(...,
                            description="The session ID of the EEG data session.")
    mode: EEGMode = Field(
        ..., description="The mode of EEG data recording, either calibration or classification.")
    timestamp_epoch: datetime = Field(
        ..., description="Timestamp of the EEG data point in epoch time.")
    channel_labels: List[str] = Field(...,
                                      description="Labels for each EEG channel.")
    data: List[List[float]] = Field(
        ..., description="Nested list of EEG data points, where each inner list corresponds to a channel and contains data points for that channel.")
    sampling_rate: int = Field(...,
                               description="The ideal sampling rate in Hz.")
    markers: Optional[List[EEGMarker]] = Field(
        default=None, description="Optional markers associated with the EEG data.")

    @validator('data')
    def validate_data(cls, v, values, **kwargs):
        mode = values.get('mode')
        if mode == EEGMode.CALIBRATION:
            # Implement any calibration-specific validation logic
            pass
        elif mode == EEGMode.CLASSIFICATION:
            # Implement any classification-specific validation logic
            pass
        return v

    class Config:
        use_enum_values = True



class CalibrationInstruction(BaseModel):
    time: int = Field(...,
                      description="Time in seconds when the instruction should be displayed")
    action: CueType = Field(...,
                            description="The specific action or instruction for the user")


class CalibrationStartResponse(BaseModel):
    message: str
    sessionId: str = Field(...,
                           description="A unique identifier for the calibration session")
    protocol: List[CalibrationInstruction]
    start_time: str = Field(...,
                            description="ISO8601 timestamp of the calibration session start time")


class ClassificationStartRequest(BaseModel):
    modelId: str = Field(...,
                         description="The model ID to use for real-time classification")


class ClassificationStartResponse(BaseModel):
    message: str
    sessionId: str = Field(...,
                           description="A unique identifier for the classification session")


class ClassificationResult(BaseModel):
    state: str = Field(...,
                       description="The classified state, e.g., 'Imagined Walking', 'Rest'")
    timestamp: str = Field(...,
                           description="ISO8601 timestamp of the classification result")
