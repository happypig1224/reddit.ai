"""
Standard Uniform API Response Wrapper
"""

from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: Optional[T] = None

    @classmethod
    def success(cls, data: Optional[T] = None, message: str = "success") -> "ApiResponse[T]":
        return cls(code=200, message=message, data=data)

    @classmethod
    def error(cls, message: str = "error", code: int = 400, data: Optional[Any] = None) -> "ApiResponse[Any]":
        return cls(code=code, message=message, data=data)

