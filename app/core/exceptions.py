from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError

class CustomException(Exception):
    def __init__(self, message: str, status_code: int = 400, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details

def setup_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(CustomException)
    async def custom_exception_handler(request: Request, exc: CustomException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "data": None, "error": exc.message, "meta": exc.details}
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = jsonable_encoder(exc.errors())
        error_msg = "; ".join([f"{err['loc'][-1]}: {err['msg']}" for err in errors])
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"success": False, "data": None, "error": f"Validation Error: {error_msg}", "meta": {"details": errors}}
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "data": None, "error": exc.detail, "meta": None}
        )

    @app.exception_handler(IntegrityError)
    async def integrity_exception_handler(request: Request, exc: IntegrityError):
        # Database conflicts (e.g., unique key violations)
        orig_msg = str(exc.orig) if exc.orig else str(exc)
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "success": False,
                "data": None,
                "error": "Database integrity violation. Resource may already exist or constraint failed.",
                "meta": {"details": orig_msg}
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "data": None, "error": f"Internal Server Error: {str(exc)}", "meta": None}
        )
