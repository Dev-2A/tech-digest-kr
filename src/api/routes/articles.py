from fastapi import APIRouter, Query

from src.storage.database import Database

router = APIRouter(prefix="/api/articles", tags=["Articles"])
db = Database()


@router.get("")
def get_articles(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    is_read: bool | None = None,
    tag: str | None = None,
):
    """글 목록 조회"""
    articles = db.get_articles(
        limit=limit, offset=offset, is_read=is_read, tag=tag
    )
    return {"articles": articles, "count": len(articles)}


@router.get("/{article_id}")
def get_article(article_id: int):
    """글 상세 조회"""
    article = db.get_article_by_id(article_id)
    if not article:
        return {"error": "글을 찾을 수 없습니다."}
    return article


@router.post("/{article_id}/read")
def mark_read(article_id: int):
    """글 읽음 처리"""
    db.mark_as_read(article_id)
    return {"message": "읽음 처리 완료", "article_id": article_id}


@router.post("/{article_id}/bookmark")
def toggle_bookmark(article_id: int):
    """북마크 토글"""
    new_state = db.toggle_bookmark(article_id)
    return {
        "message": "북마크 변경 완료",
        "article_id": article_id,
        "is_bookmarked": new_state,
    }