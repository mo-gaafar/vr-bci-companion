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

