from fastapi import APIRouter

from src.api.schemas import InterestTagsRequest
from src.storage.database import Database

router = APIRouter(prefix="/api/settings", tags=["Settings"])
db = Database()


@router.get("/tags")
def get_interest_tags():
    """관심 태그 목록 조회"""
    tags = db.get_interest_tags()
    if not tags:
        from config.settings import settings
        return {"tags": [{"tag": t, "weight": 1.0} for t in settings.default_interest_tags]}
    return {"tags": tags}


@router.put("/tags")
def update_interest_tags(request: InterestTagsRequest):
    """관심 태그 업데이트"""
    db.set_interest_tags(request.tags)
    return {"message": "관심 태그가 업데이트되었습니다.", "tags": request.tags}


@router.get("/stats")
def get_stats():
    """전체 통계 조회"""
    return db.get_stats()