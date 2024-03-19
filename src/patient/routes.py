from bson import ObjectId

import pymongo
from .models import PatientOut, PatientInDB, PatientSignup, ExerciseRecord
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List

from patient.models import PatientInDB, ExerciseRecord, PatientUpdate
from common.models import SuccessfulResponse
from patient.repo import PatientRepository

router = APIRouter(prefix="/patient")

# Database dependency


def get_patient_repo():
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    yield PatientRepository(client)

# ... Rest of your routes ... (See previous examples for the full structure)


@router.post("/signup", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
async def signup(patient: PatientSignup, repo: PatientRepository = Depends(get_patient_repo)):
    # creates a new auth user and then creates a new patient
    from .service import patient_signup
    return await patient_signup(patient, repo)


# @router.post("/", response_model=Patient, status_code=status.HTTP_201_CREATED)
# async def create_patient(patient: Patient, repo: PatientRepository = Depends(get_patient_repo)):
#     return await repo.create_patient(patient)


@router.get("/{patient_id}", response_model=PatientOut)
async def get_patient(patient_id: str, repo: PatientRepository = Depends(get_patient_repo)):
    patient = await repo.get_patient(patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient


@router.get("/", response_model=List[PatientOut])
async def get_all_patients(repo: PatientRepository = Depends(get_patient_repo)):
    return await repo.get_all_patients()


@router.put("/{patient_id}", response_model=PatientOut)
async def update_patient(
    patient_id: str, update_data: PatientUpdate, repo: PatientRepository = Depends(get_patient_repo)
):
    updated_patient = await repo.update_patient(patient_id, update_data)
    if not updated_patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return updated_patient


@router.delete("/{patient_id}", response_model=SuccessfulResponse)
async def delete_patient(patient_id: str, repo: PatientRepository = Depends(get_patient_repo)):
    if not await repo.delete_patient(patient_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return SuccessfulResponse()


@router.post("/{patient_id}/exercises", response_model=ExerciseRecord, status_code=status.HTTP_201_CREATED)
async def add_exercise_record(
    patient_id: str, record: ExerciseRecord, repo: PatientRepository = Depends(get_patient_repo)
):
    record.patient_id = ObjectId(patient_id)  # Associate with the patient
    return await repo.add_exercise_record(record)


@router.get("/{patient_id}/exercises", response_model=List[ExerciseRecord])
async def get_patient_exercises(patient_id: str, repo: PatientRepository = Depends(get_patient_repo)):
    return await repo.get_patient_exercise_records(patient_id)
