from fastapi.responses import JSONResponse
from fastapi import APIRouter

from server.auth.routes import auth
from server.patient.routes import router as patient


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

api_router.include_router(auth, tags=["auth"])
api_router.include_router(patient, tags=["patient"])

