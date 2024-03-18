
from fastapi import Depends
from patient.repo import PatientRepository
from .models import PatientSignup


def patient_signup(signup: Patient, repo: PatientRepository = Depends(get_patient_repo)):
    # creates a new auth user and then creates a new patient
    return await repo.create_patient(signup)