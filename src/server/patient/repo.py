import pymongo
from bson import ObjectId
from typing import List

from typing import Optional
from .models import PatientOut, ExerciseRecord, PatientUpdate, PatientInDB
from server.database import MongoDB


class PatientRepository:
    def __init__(self):
        self.db = MongoDB
        self.patient_collection = self.db.patients
        self.exercise_record_collection = self.db.exercise_records

    def create_patient(self, patient: PatientInDB) -> PatientInDB:
        result = self.patient_collection.insert_one(patient.dict())
        patient.id = result.inserted_id
        return patient

    def get_patient(self, patient_id: str) -> Optional[PatientInDB]:
        patient_data = self.patient_collection.find_one(
            {"_id": ObjectId(patient_id)})
        if patient_data:
            return PatientInDB(**patient_data)
        return None

    def get_all_patients(self) -> List[PatientInDB]:
        cursor = self.patient_collection.find()
        patients = cursor.to_list(length=None)  # Get all results
        return [PatientInDB(**document) for document in patients]

    def update_patient(self, patient_id: str, update_data: PatientUpdate) -> Optional[PatientInDB]:
        update_dict = {k: v for k, v in update_data.dict().items()
                       if v is not None}

        if update_dict:
            result = self.patient_collection.update_one(
                {"_id": ObjectId(patient_id)}, {"$set": update_dict}
            )
            if result.matched_count:
                return self.get_patient(patient_id)

        return None

    def delete_patient(self, patient_id: str) -> bool:
        result = self.patient_collection.delete_one(
            {"_id": ObjectId(patient_id)})
        return result.deleted_count > 0

    def add_exercise_record(self, record: ExerciseRecord) -> ExerciseRecord:
        result = self.exercise_record_collection.insert_one(record.dict())
        record.id = result.inserted_id
        return record

    def get_patient_exercise_records(self, patient_id: str) -> List[ExerciseRecord]:
        cursor = self.exercise_record_collection.find(
            {"patient_id": ObjectId(patient_id)})
        records = cursor.to_list(length=None)
        return [ExerciseRecord(**document) for document in records]
