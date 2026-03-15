from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import database
from routers import auth, companies, reference, profiler, comparisons

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.init_pool()
    yield
    await database.close_pool()

app = FastAPI(title="Job Choice OS API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(companies.router, prefix="/api/v1/companies", tags=["companies"])
app.include_router(reference.router, prefix="/api/v1/reference", tags=["reference"])
app.include_router(profiler.router, prefix="/api/v1/profiler", tags=["profiler"])
app.include_router(comparisons.router, prefix="/api/v1/comparisons", tags=["comparisons"])

@app.get("/api/v1/health")
async def health():
    return {"status": "ok"}
