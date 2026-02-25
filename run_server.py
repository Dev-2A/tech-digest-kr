"""Tech Digest KR API 서버 실행"""
import uvicorn

from config.settings import settings


if __name__ == "__main__":
    uvicorn.run(
        "src.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )