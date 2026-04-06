from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import config
import database
from routers import auth, companies, reference, profiler, comparisons, landing, admin, oauth
from middleware.rate_limiter import RateLimitMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.init_pool()
    yield
    await database.close_pool()

app = FastAPI(title="Job Choice OS API", version="1.0.0", lifespan=lifespan)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(companies.router, prefix="/api/v1/companies", tags=["companies"])
app.include_router(reference.router, prefix="/api/v1/reference", tags=["reference"])
app.include_router(profiler.router, prefix="/api/v1/profiler", tags=["profiler"])
app.include_router(comparisons.router, prefix="/api/v1/comparisons", tags=["comparisons"])
app.include_router(landing.router, prefix="/api/v1/landing", tags=["landing"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(oauth.router, prefix="/api/v1/oauth", tags=["oauth"])

@app.get("/api/v1/health")
async def health():
    return {"status": "ok"}
