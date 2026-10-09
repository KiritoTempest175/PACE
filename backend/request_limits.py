"""ASGI upload/body ceiling applied *before* multipart parsing.

File-level validation still runs in upload_service. This middleware protects
against oversized multipart parsing and Content-Length bypass (chunked bodies).
"""
from __future__ import annotations

from fastapi.responses import JSONResponse
from core.config import get_settings


class TooLarge(Exception):
    pass


class RequestBodyLimit:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        limit = get_settings().max_upload_bytes + 64 * 1024
        headers = dict(scope.get("headers") or [])
        length = headers.get(b"content-length")
        if length is not None:
            try:
                if int(length) > limit:
                    await JSONResponse({"detail": "Request body exceeds limit"}, status_code=413)(scope, receive, send)
                    return
            except ValueError:
                await JSONResponse({"detail": "Invalid Content-Length"}, status_code=400)(scope, receive, send)
                return
        consumed = 0

        async def bounded_receive():
            nonlocal consumed
            event = await receive()
            if event["type"] == "http.request":
                consumed += len(event.get("body", b""))
                if consumed > limit:
                    raise TooLarge()
            return event

        try:
            await self.app(scope, bounded_receive, send)
        except TooLarge:
            await JSONResponse({"detail": "Request body exceeds limit"}, status_code=413)(scope, receive, send)
