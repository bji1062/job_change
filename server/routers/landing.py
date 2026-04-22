"""랜딩 라우터 — 비즈니스 로직은 services/landing_service 로 위임."""
from fastapi import APIRouter
from models.landing import PingReq
from services import landing_service

router = APIRouter()


@router.get("/feed")
async def get_feed():
    return await landing_service.fetch_feed()


@router.get("/stats")
async def get_stats():
    return await landing_service.fetch_stats()


@router.get("/popular")
async def get_popular():
    return await landing_service.fetch_popular()


@router.post("/popular/{case_id}/view")
async def increment_view(case_id: int):
    view_no = await landing_service.increment_case_view(case_id)
    return {"view_no": view_no}


@router.post("/ping")
async def ping(req: PingReq):
    return await landing_service.record_ping(req.client_id)
