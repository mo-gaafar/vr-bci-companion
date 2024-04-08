from common.exceptions import RepositoryException
from pydantic import ValidationError
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse


# @app.exception_handler(Exception)
async def common_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error, unhandled exception. Please contact the administrator.",
                 "details": str(exc)},
    )

# @app.exception_handler(RepositoryException)


async def repository_exception_handler(request: Request, exc: RepositoryException):
    return JSONResponse(
        status_code=400,
        content={"message": "Data validation error",
                 "details": str(exc)},
    )


# @app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )


# @app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={"message": "Validation error", "details": exc.errors()},
    )
