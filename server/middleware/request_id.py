"""Request ID middleware — 구조화 로깅 + 요청 추적용.

contextvar 에 request_id 를 주입해 logger 가 자동으로 포함.
응답 헤더 X-Request-Id 로도 노출해 클라이언트 디버깅 지원.
"""
import uuid
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware

_request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


def get_request_id() -> str:
    return _request_id_ctx.get()


class RequestIdMiddleware(BaseHTTPMiddleware):
    """요청당 고유 ID 생성/전파. 클라이언트가 X-Request-Id 를 보내면 채택, 없으면 uuid4."""

    async def dispatch(self, request, call_next):
        rid = request.headers.get("X-Request-Id") or uuid.uuid4().hex[:12]
        token = _request_id_ctx.set(rid)
        try:
            response = await call_next(request)
            response.headers["X-Request-Id"] = rid
            return response
        finally:
            _request_id_ctx.reset(token)


class RequestIdLogFilter:
    """logger format 에 %(request_id)s 를 사용할 수 있도록 LogRecord 에 request_id 주입.

    logging.Filter 인터페이스를 충족하도록 filter(record) 를 구현.
    """

    def filter(self, record):
        record.request_id = _request_id_ctx.get()
        return True
