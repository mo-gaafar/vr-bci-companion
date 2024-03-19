
from fastapi import Depends
from patient.repo import PatientRepository
from .models import PatientSignup, PatientInDB
from .repo import PatientRepository


def patient_signup(signup: PatientSignup, repo: PatientRepository):
    # creates a new auth user and then creates a new patient
    from auth.repo import create_auth_user
    from auth.models import UserIn
    user_in = UserIn(
        username=signup.username,
        password=signup.password,
        email=signup.email,
        phone=signup.phone,
        role="patient"
    )
    user = create_auth_user(user_in)
    signup = PatientInDB(**signup.dict(), auth_user_id=user.id)
    return repo.create_patient(signup)
