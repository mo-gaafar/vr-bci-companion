from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from enum import Enum, auto


class ConnectionStatus(str, Enum):
    CONNECTED = "Connected"
    DISCONNECTED = "Disconnected"
    RECONNECTING = "Reconnecting"
    ERROR = "Error"
    TIMEOUT = "Timeout"


class CalibrationAction(BaseModel):
    """Protocol for the calibration session"""
    baseline: Optional[float] = Field(None,
                                      description="How long the baseline is, before the action is performed.")
    time: float = Field(...,
                        description="Time in seconds when the instruction should be displayed")
    cooldown: Optional[float] = Field(None,
                                      description="How long the cooldown is, after the action is performed.")
    action: str = Field(...,
                        description="The specific action or instruction for the user")
    label: Optional[str] = Field(None,
                                 description="The label of the action")


class CalibrationSet(BaseModel):

    repeat: int = Field(...,
                        description="Number of times to repeat the action set")
    actions: List[CalibrationAction] = Field(...,
                                             description="List of calibration actions")


class CalibrationProtocol(BaseModel):
    """Protocol for the calibration session"""
    prepare: CalibrationSet = Field(...,
                                    description="Prepare the user for the calibration session")
    main_trial: CalibrationSet = Field(...,
                                       description="Main trial of the calibration session")
    end: CalibrationSet = Field(...,
                                description="End the calibration session")


class SessionState(str, Enum):
    UNSTARTED = "Unstarted"
    CALIBRATION = "Calibration"
    TRAINING = "Training"
    READY_FOR_CLASSIFICATION = "Ready for Classification"
    CLASSIFICATION = "Classification"
    CLOSED = "Closed"


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


class EEGChunk(BaseModel):
    data: List[List]
    timestamps: List


class ElectrodeCoordinate(BaseModel):
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    z: float = Field(..., description="Z coordinate")


class EEGSpecification(BaseModel):
    """Specifications of the acquisition modalities"""
    channel_labels: List[str] = []
    electrode_placement: Dict[str, ElectrodeCoordinate] = Field(
        ..., description="Dictionary mapping electrode labels to their coordinates")
    amplifier: str = Field(..., description="The EEG amplifier used.")
    amplificatoin_gain: List[int] = Field(...,
                                          description="The amplification gain.")
    sampling_rate: int = Field(..., description="The sampling rate in Hz.")
    resolution: int = Field(..., description="The resolution in bits.")
    filter_bandwidth: List[int] = Field(...,
                                        description="The filter bandwidth in Hz.")


class EEGData(BaseModel):
    session_id: str = Field(...,
                            description="The session ID of the EEG data session.")
    mode: EEGMode = Field(
        ..., description="The mode of EEG data recording, either calibration or classification.")
    timestamps: List = Field(
        [], description="Timestamp of the EEG data point in epoch time.")
    data: List[List[float]] = Field(
        ..., description="Nested list of EEG data points, where each inner list corresponds to a channel and contains data points for that channel.")
    sampling_rate: int = Field(...,
                               description="The ideal sampling rate in Hz.")
    markers: Optional[List[EEGMarker]] = Field(
        default=None, description="Optional markers associated with the EEG data.")

    @field_validator('data')
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


class CalibrationStartResponse(BaseModel):
    message: str
    session_id: str = Field(...,
                            description="A unique identifier for the calibration session")
    protocol: CalibrationProtocol
    start_time: str = Field(...,
                            description="ISO8601 timestamp of the calibration session start time")


class ClassificationStartRequest(BaseModel):
    ml_model_id: str = Field(...,
                             description="The model ID to use for real-time classification")
    session_id: str = Field(...,
                            description="The session ID of the classification session")


class ClassificationStartResponse(BaseModel):
    message: str = "Classification started"
    session_id: str = Field(...,
                            description="A unique identifier for the classification session")


class ClassificationResult(BaseModel):
    state: str = Field(...,
                       description="The classified state, e.g., 'Imagined Walking', 'Rest'")
    timestamp: datetime = Field(...,
                                description="ISO8601 timestamp of the classification result")
    issued_at: datetime = Field(...,
                                description="ISO8601 timestamp of when the classification result was issued")


class ServersEnum(str, Enum):
    local = "local"
    heroku = "heroku"
    aws = "aws"


class ConnectionLog(BaseModel):
    timestamp: datetime = Field(...,
                                description="ISO8601 timestamp of the connection log")
    status: ConnectionStatus = Field(...,
                                     description="The connection status")
    message: str = Field(...,
                         description="The connection message")


class ClassificatoinLog(BaseModel):
    timestamp: datetime = Field(...,
                                description="ISO8601 timestamp of the classification log")
    message: str = Field(...,
                         description="The classification message")
    issued_at: str = Field(...,
                           description="ISO8601 timestamp of when the classification result was issued")
    output: str = Field(...,
                        description="The classification output")


class SessionInDB(BaseModel):
    session_id: str = Field(...,
                            description="A unique identifier for the session")
    state: SessionState = Field(...,
                                description="The state of the session")
    start_time: str = Field(...,
                            description="ISO8601 timestamp of the session start time")
    end_time: Optional[str] = Field(
        None, description="ISO8601 timestamp of the session end time")

    protocol: Optional[CalibrationProtocol] = Field(
        None, description="The calibration protocol used in the session")

    ml_model_id: Optional[str] = Field(
        None, description="The model ID used in the session", alias="model_id")
    ml_model_repo: Optional[str] = Field(
        None, description="The model repository used in the session")
    ml_model_path: Optional[str] = Field(
        None, description="The model path used in the session")
    ml_model_version: Optional[str] = Field(
        None, description="The model version used in the session")

    classification_state: Optional[str] = Field(
        None, description="The current classification state")
    last_classification_result: Optional[ClassificationResult] = Field(
        None, description="The last classification result")

    connection_logs: List[str] = Field(
        [], description="List of connection logs for the session")
    classification_logs: List[str] = Field(
        [], description="List of classification logs for the session")

    running_on: Optional[ServersEnum] = Field(
        None, description="The server where the session is running")
