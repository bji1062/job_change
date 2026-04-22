import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import config
import database
from routers import auth, companies, reference, profiler, comparisons, landing, admin, oauth
from middleware.rate_limiter import RateLimitMiddleware
from middleware.request_id import RequestIdMiddleware, RequestIdLogFilter


def _setup_logging() -> None:
    root = logging.getLogger()
    # 기존 핸들러(uvicorn default) 가 있으면 우리 포맷을 덮어씀
    for h in list(root.handlers):
        root.removeHandler(h)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s [%(request_id)s] %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    handler.addFilter(RequestIdLogFilter())
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    # uvicorn 로거들은 자체 핸들러만 쓰고 root 로 propagate 하지 않도록 설정 (중복 출력 방지)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        lg = logging.getLogger(name)
        lg.handlers = [handler]
        lg.propagate = False


_setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app starting — initializing DB pool")
    await database.init_pool()
    yield
    logger.info("app stopping — closing DB pool")
    await database.close_pool()

app = FastAPI(title="Job Choice OS API", version="1.0.0", lifespan=lifespan)

# RequestId 먼저 깔아야 이후 미들웨어/라우터 로그에 request_id 주입됨
app.add_middleware(RequestIdMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-Request-Id"],
    expose_headers=["X-Request-Id"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(companies.router, prefix="/api/v1/companies", tags=["companies"])
app.include_router(reference.router, prefix="/api/v1/reference", tags=["reference"])
app.include_router(profiler.router, prefix="/api/v1/profiler", tags=["profiler"])
app.include_router(comparisons.router, prefix="/api/v1/comparisons", tags=["comparisons"])
app.include_router(landing.router, prefix="/api/v1/landing", tags=["landing"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(oauth.router, prefix="/api/v1/oauth", tags=["oauth"])


# ━━ HEALTH CHECKS ━━
# /live: 프로세스 살아있음만 — systemd/nginx 재시작 트리거용 (DB 장애에 강건)
# /ready: DB 풀 확인 — 로드밸런서/OCI 헬스체크용 (DB 죽으면 트래픽 차단)
@app.get("/api/v1/health")
async def health():
    """레거시 — /live 와 동일. 하위 호환용."""
    return {"status": "ok"}


@app.get("/api/v1/live")
async def live():
    """Liveness probe — 프로세스만 체크."""
    return {"status": "ok"}


@app.get("/api/v1/ready")
async def ready():
    """Readiness probe — DB 연결까지 확인."""
    try:
        row = await database.fetch_one("SELECT 1 AS ok")
        if row and row.get("ok") == 1:
            return {"status": "ok", "db": "ok"}
        return {"status": "degraded", "db": "unexpected"}, 503
    except Exception as e:
        logger.warning("readiness check failed: %s", e)
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=503, content={"status": "not_ready", "db": "error"})
