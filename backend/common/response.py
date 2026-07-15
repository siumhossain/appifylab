from fastapi.responses import JSONResponse
from fastapi import Response
from fastapi.encoders import jsonable_encoder

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from typing import Any, Optional
import uuid
import datetime
from decimal import Decimal


def _serialize(obj: Any) -> Any:
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize(i) for i in obj]
    return obj


ERROR_CODE_STATUS_MAP = {
    "NOT_FOUND": 404,
    "UNAUTHORIZED": 401,
    "PERMISSION_DENIED": 403,
    "ALREADY_EXISTS": 409,
    "VALIDATION_ERROR": 422,
    "INSUFFICIENT_STOCK": 409,
    "INVALID_OPERATION": 400,
    "DEPENDENCY_ERROR": 400,
    "DATABASE_ERROR": 500,
    "UNKNOWN_ERROR": 400,
}


def resolve_status_code(error_code) -> int:
    if error_code is None:
        return 400
    code = error_code.value if hasattr(error_code, "value") else str(error_code)
    return ERROR_CODE_STATUS_MAP.get(code, 400)


def result_response(result, status_code: int = 200):
    if not result.success:
        return CustomResponse.error(
            message=result.message,
            status_code=resolve_status_code(result.error_code),
            extra_fields=result.to_dict()
        )
    return CustomResponse.success(data=result.data, message=result.message, status_code=status_code)


class CustomException(Exception):
    def __init__(self, message: str = "Issue", status_code: int = 400, headers: Optional[dict[str, str]] = None, extra_fields: Optional[dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.headers = headers
        self.extra_fields = extra_fields

class CustomResponse:

    @classmethod
    def success(
        cls,
        data: list = [],
        message: str = "success",
        status_code: int = 200,
        extra_fields: dict = [],
    ) -> dict | list:
        if data:
            return cls._build_response(data, message, status_code, extra_fields)
        return cls._build_response(
            data=data,
            message=message,
            status_code=status_code,
            extra_fields=extra_fields,
        )

    @classmethod
    def basic_response(
        cls,
        data: list = [],
        message: str = "successfully retrive",
        status_code: int = 200,
        extra_fields: dict = [],
    ) -> dict | list:
        return cls._build_response(data, message, status_code, extra_fields)

    @classmethod
    def error(
        cls,
        message: str = "Something wrong",
        status_code: int = 400,
        extra_fields: dict = [],
    ) -> dict:
        return cls._build_response(None, message, status_code, extra_fields)

    @staticmethod
    def _build_response(
        data: dict, message: str, status_code: int, extra_fields: dict = []
    ) -> list | dict:
        response_data = {"results": _serialize(data), "message": message}
        if extra_fields:
            response_data.update(_serialize(extra_fields))
        return JSONResponse(content=response_data, status_code=status_code)