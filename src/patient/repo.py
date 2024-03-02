import pymongo
from bson import ObjectId
from typing import List
from .models import Patient, ExerciseRecord, PatientUpdate


class PatientRepository:
    def __init__(self, db_client: pymongo.MongoClient):
        self.db = db_client.your_database_name
        self.patient_collection = self.db.patients
        self.exercise_record_collection = self.db.exercise_records

    async def create_patient(self, patient: Patient) -> Patient:
        result = await self.patient_collection.insert_one(patient.dict())
        patient.id = result.inserted_id
        return patient

    async def get_patient(self, patient_id: str) -> Patient | None:
        patient_data = await self.patient_collection.find_one({"_id": ObjectId(patient_id)})
        if patient_data:
            return Patient(**patient_data)
        return None

    async def get_all_patients(self) -> List[Patient]:
        cursor = self.patient_collection.find()
        patients = await cursor.to_list(length=None)  # Get all results
        return [Patient(**document) for document in patients]

    async def update_patient(self, patient_id: str, update_data: PatientUpdate) -> Patient | None:
        update_dict = {k: v for k, v in update_data.dict().items()
                       if v is not None}

        if update_dict:
            result = await self.patient_collection.update_one(
                {"_id": ObjectId(patient_id)}, {"$set": update_dict}
            )
            if result.matched_count:
                return await self.get_patient(patient_id)

        return None

    async def delete_patient(self, patient_id: str) -> bool:
        result = await self.patient_collection.delete_one({"_id": ObjectId(patient_id)})
        return result.deleted_count > 0

    async def add_exercise_record(self, record: ExerciseRecord) -> ExerciseRecord:
        result = await self.exercise_record_collection.insert_one(record.dict())
        record.id = result.inserted_id
        return record

    async def get_patient_exercise_records(self, patient_id: str) -> List[ExerciseRecord]:
        cursor = self.exercise_record_collection.find(
            {"patient_id": ObjectId(patient_id)})
        records = await cursor.to_list(length=None)
        return [ExerciseRecord(**document) for document in records]
