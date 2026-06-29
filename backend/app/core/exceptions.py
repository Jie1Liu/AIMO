from __future__ import annotations
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AimoError(Exception):
    status_code = 400

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class NotFoundError(AimoError):
    status_code = 404


class PolicyError(AimoError):
    status_code = 409


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AimoError)
    async def handle_aimo_error(_: Request, exc: AimoError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
