from bson import ObjectId
import pymongo
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List

from .repo import PatientRepository
from .models import PatientOut, PatientInDB, PatientSignup, ExerciseRecord
from .models import PatientInDB, ExerciseRecord, PatientUpdate
from server.auth.service import verify_token_header
from server.common.util.security import access_check
from server.common.models import SuccessfulResponse

router = APIRouter(prefix="/patient")

# Database dependency


def get_patient_repo():
    return PatientRepository()


@router.post("/signup", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
async def signup(patient: PatientSignup, repo: PatientRepository = Depends(get_patient_repo)):
    # creates a new auth user and then creates a new patient
    from .service import patient_signup
    # try:
    patient = patient_signup(patient, repo)
    return patient
    # except Exception as e:
    # raise HTTPException(
    #     status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# @router.post("/", response_model=Patient, status_code=status.HTTP_201_CREATED)
# async def create_patient(patient: Patient, repo: PatientRepository = Depends(get_patient_repo)):
#     return await repo.create_patient(patient)


@router.get("/{patient_id}", response_model=PatientOut)
async def get_patient(patient_id: str, repo: PatientRepository = Depends(get_patient_repo), auth_user=Depends(verify_token_header)):
    patient = await repo.get_patient(patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient


@router.get("/", response_model=List[PatientOut])
async def get_all_patients(repo: PatientRepository = Depends(get_patient_repo), auth_user=Depends(verify_token_header)):
    access_check(auth_user, ["admin", "doctor"])
    return await repo.get_all_patients()


@router.put("/{patient_id}", response_model=PatientOut)
async def update_patient(
    patient_id: str, update_data: PatientUpdate, repo: PatientRepository = Depends(get_patient_repo), auth_user=Depends(verify_token_header)
):
    access_check(auth_user, ["admin", "doctor", "patient"])
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
