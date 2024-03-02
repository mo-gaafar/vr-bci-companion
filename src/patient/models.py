from bson import ObjectId
from pydantic import BaseModel, Field, validator
from datetime import datetime
from models import PyObjectId

from models import MongoBaseModel


class Patient(MongoBaseModel):
    name: str
    age: int
    medical_history: str
    rehabilitation_program: str

    class Config:
        schema_extra = {
            "example": {
                "name": "Jane Doe",
                "age": 35,
                "medical_history": "Previous ACL surgery",
                "rehabilitation_program": "Post-operative Knee Recovery"
            }
        }


class ExerciseRecord(MongoBaseModel):
    patient_id: PyObjectId
    exercise_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    performance_metrics: dict

    class Config:
        schema_extra = {
            "example": {
                "patient_id": "63dd03cbef0772c28037964c",
                "exercise_name": "Squats",
                "timestamp": "2024-03-02T16:23:00",
                "performance_metrics": {
                    "repetitions": 15,
                    "range_of_motion": 85,
                    # ... add any other relevant metrics
                }
            }
        }


class PatientUpdate(BaseModel):
    name: str | None = None
    age: int | None = None
    medical_history: str | None = None
    rehabilitation_program: str | None = None
