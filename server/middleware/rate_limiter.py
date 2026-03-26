import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# 엔드포인트별 분당 요청 제한
_RATE_LIMITS = {
    "/api/v1/auth/login": 10,
    "/api/v1/auth/register": 5,
}
_DEFAULT_LIMIT = 60
_WINDOW = 60  # seconds

# IP별 요청 타임스탬프 저장
_requests: dict[str, list[float]] = defaultdict(list)
_last_cleanup = time.time()


def _cleanup():
    """오래된 타임스탬프 정리 (5분마다)."""
    global _last_cleanup
    now = time.time()
    if now - _last_cleanup < 300:
        return
    _last_cleanup = now
    cutoff = now - _WINDOW
    stale = [k for k, v in _requests.items() if not v or v[-1] < cutoff]
    for k in stale:
        del _requests[k]


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # health 체크는 제한 없음
        if request.url.path == "/api/v1/health":
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        path = request.url.path
        limit = _RATE_LIMITS.get(path, _DEFAULT_LIMIT)
        key = f"{ip}:{path}"

        now = time.time()
        cutoff = now - _WINDOW

        # 슬라이딩 윈도우: 윈도우 밖 타임스탬프 제거
        timestamps = _requests[key]
        while timestamps and timestamps[0] < cutoff:
            timestamps.pop(0)

        if len(timestamps) >= limit:
            return JSONResponse(
                status_code=429,
                content={"detail": f"요청이 너무 많습니다. {_WINDOW}초 후 다시 시도해주세요."},
            )

        timestamps.append(now)
        _cleanup()
        return await call_next(request)
