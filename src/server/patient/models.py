from pydantic import EmailStr
from typing import Optional
from typing import Annotated
from bson import ObjectId
from pydantic import BaseModel, Field, validator
from datetime import datetime

from server.common.models import MongoBaseModel, ObjectIdPydanticAnnotation
from server.common.models import ObjectIdPydanticAnnotation


class PatientOut(MongoBaseModel):
    first_name: str
    last_name: str
    date_of_birth: datetime
    medical_history: str
    rehabilitation_program: str
    diagnosis: Optional[str] = None

    # class Config:
    #     json_schema_extra = {
    #         "example": {
    #             "name": "Jane Doe",
    #             "age": 35,
    #             "medical_history": "Previous ACL surgery",
    #             "rehabilitation_program": "Post-stroke rehabilitation program",
    #             "diagnosis": "Hemi-paresis due to stroke"
    #         }
    #     }


class PatientSignup(BaseModel):
    username: str
    password: str
    email: EmailStr
    phone: str
    first_name: str
    last_name: str
    date_of_birth: datetime
    medical_history: str
    rehabilitation_program: str
    diagnosis: Optional[str] = None


class ExerciseRecord(MongoBaseModel):
    patient_id: Annotated[ObjectId, ObjectIdPydanticAnnotation]
    exercise_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    performance_metrics: dict

    class Config:
        json_schema_extra = {
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
    name: Optional[str] = None
    age: Optional[int] = None
    medical_history: Optional[str] = None
    rehabilitation_program: Optional[str] = None


class PatientInDB(MongoBaseModel):
    first_name: str
    last_name: str
    date_of_birth: datetime
    medical_history: str
    rehabilitation_program: str
    diagnosis: Optional[str] = None
    auth_user_id: Optional[Annotated[ObjectId,
                                     ObjectIdPydanticAnnotation]] = None
