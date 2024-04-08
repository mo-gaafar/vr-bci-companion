from auth.routes import auth
from patient.routes import router as patient
from fastapi import APIRouter
from fastapi.responses import JSONResponse


api_router = APIRouter(
    default_response_class=JSONResponse,
    # responses={
    #     400: {"model": ErrorResponse},
    #     401: {"model": ErrorResponse},
    #     403: {"model": ErrorResponse},
    #     404: {"model": ErrorResponse},
    #     500: {"model": ErrorResponse},
    # },
)
