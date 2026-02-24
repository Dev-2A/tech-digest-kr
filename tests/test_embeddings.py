"""임베딩 + 글 분류 수동 테스트"""
import numpy as np

from src.embeddings.embedding_service import EmbeddingService, ArticleClassifier
from src.collectors.models import FeedEntry
from datetime import datetime, timezone


def make_dummy_entry(title: str, tags: list[str]) -> dict:
    """테스트용 더미 글 생성"""
    entry = FeedEntry(
        title=title,
        url=f"https://example.com/{title.replace(' ', '-')}",
        author="tester",
        published=datetime.now(tz=timezone.utc),
        content=title,
        platform="test",
        feed_name="test feed",
        tags=tags,
    )
    return {
        "entry": entry,
        "summary": {"summary": title, "lines": [title], "success": True},
        "tags": tags,
    }


def main():
    svc = EmbeddingService()

    # 1. 기본 임베딩 테스트
    print("=== 기본 임베딩 테스트 ===\n")
    texts = [
        "FastAPI로 REST API 서버 만들기",
        "Django와 FastAPI 비교 분석",
        "스타듀밸리 농사 가이드",
    ]
    vectors = svc.encode_batch(texts)
    print(f"벡터 차원: {vectors.shape}")

    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            sim = svc.cosine_similarity(vectors[i], vectors[j])
            print(f"  '{texts[i][:20]}...' ↔ '{texts[j][:20]}...' = {sim:.4f}")

    # 2. 글 분류 테스트
    print(f"\n=== 글 분류 테스트 ===\n")

    # 읽은 글 (Python/백엔드 관련)
    read_texts = [
        "Python FastAPI 튜토리얼 태그: python, fastapi, backend",
        "SQLAlchemy ORM 사용법 태그: python, database, orm",
        "Docker로 개발환경 구축 태그: docker, devops",
    ]
    read_vectors = svc.encode_batch(read_texts)

    # 새 글 후보
    new_articles = [
        make_dummy_entry("FastAPI 미들웨어 작성법", ["python", "fastapi"]),
        make_dummy_entry("React 18 동시성 기능 소개", ["react", "frontend"]),
        make_dummy_entry("PostgreSQL 인덱스 최적화", ["database", "postgresql"]),
        make_dummy_entry("Kubernetes 오토스케일링 전략", ["kubernetes", "devops"]),
    ]

    classifier = ArticleClassifier(svc)
    classifier.update_read_history(read_vectors)
    result = classifier.classify(new_articles, threshold=0.5)

    print(f"🔄 비슷한 글 ({len(result['familiar'])}건):")
    for item in result["familiar"]:
        title = item["article"]["entry"].title
        print(f"  📖 {title} (유사도: {item['max_similarity']})")

    print(f"\n🆕 새로운 글 ({len(result['novel'])}건):")
    for item in result["novel"]:
        title = item["article"]["entry"].title
        print(f"  🔍 {title} (유사도: {item['max_similarity']})")


if __name__ == "__main__":
    main()