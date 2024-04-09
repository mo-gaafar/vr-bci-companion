from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from enum import Enum


class CueType(str, Enum):
    prepare = "Prepare"
    start_imagining_walking = "Start Imagining Walking"
    stop_and_rest = "Stop and Rest"
    repeat_or_end = "Repeat or End"


class UserInfo(BaseModel):
    user_id: str = Field(..., description="Unique identifier for the user")
    age: Optional[int] = Field(None, description="Age of the user")
    experience_level: Optional[str] = Field(
        None, description="User's experience level with BCI devices, e.g., novice, experienced")


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
