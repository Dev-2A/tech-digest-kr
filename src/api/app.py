from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from src.api.routes import articles, digest, settings

app = FastAPI(
    title="Tech Digest KR",
    description="📰 한국어 기술 블로그 RSS 수집 → LLM 3줄 요약 → 개인 뉴스레터",
    version="0.1.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(articles.router)
app.include_router(digest.router)
app.include_router(settings.router)

# 정적 파일 (프론트엔드)
static_dir = Path(__file__).parent / "templates" / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
def root():
    return {
        "name": "Tech Digest KR",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": {
            "articles": "/api/articles",
            "digest_run": "/api/digest/run",
            "digest_latest": "/api/digest/latest",
            "settings_tags": "/api/settings/tags",
            "stats": "/api/settings/stats",
        },
    }


@app.get("/health")
def health():
    return {"status": "ok"}