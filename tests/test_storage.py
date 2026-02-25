"""SQLite 저장소 수동 테스트"""
import os
import numpy as np

from src.storage.database import Database


TEST_DB = "data/test_digest.db"


def main():
    # 테스트용 DB (기존 것 삭제)
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

    db = Database(db_path=TEST_DB)
    print("✅ 테이블 초기화 완료\n")

    # 1. 글 저장
    print("=== 글 저장 테스트 ===")
    fake_embedding = np.random.rand(384).astype(np.float32)

    articles = [
        {
            "url": "https://velog.io/@test/fastapi-guide",
            "title": "FastAPI 완벽 가이드",
            "author": "dev_kim",
            "published_at": "2025-02-20T09:00:00+00:00",
            "content": "FastAPI는 현대적인 Python 웹 프레임워크입니다...",
            "platform": "velog",
            "feed_name": "velog 트렌딩",
            "tags": ["python", "fastapi", "backend"],
            "summary": "FastAPI의 핵심 기능과 사용법을 다룹니다.",
            "summary_lines": [
                "FastAPI의 비동기 처리 방식을 설명한다.",
                "Pydantic 기반 데이터 검증을 활용한다.",
                "성능과 개발 생산성 모두 뛰어나다.",
            ],
            "embedding": fake_embedding,
        },
        {
            "url": "https://velog.io/@test/react-hooks",
            "title": "React Hooks 심화",
            "author": "frontend_lee",
            "published_at": "2025-02-19T15:00:00+00:00",
            "content": "React Hooks의 고급 패턴을 알아봅시다...",
            "platform": "velog",
            "feed_name": "velog 트렌딩",
            "tags": ["react", "javascript", "frontend"],
            "summary": "React Hooks의 고급 패턴을 소개합니다.",
            "summary_lines": [
                "useReducer와 useContext 조합 패턴을 다룬다.",
                "커스텀 훅으로 로직을 재사용하는 방법을 보여준다.",
                "성능 최적화를 위한 useMemo, useCallback을 설명한다.",
            ],
            "embedding": fake_embedding,
        },
    ]

    result = db.insert_article_batch(articles)
    print(f"  저장: {result['inserted']}건, 건너뜀: {result['skipped']}건")

    # 중복 저장 테스트
    result2 = db.insert_article_batch(articles)
    print(f"  중복 재시도: 저장 {result2['inserted']}건, 건너뜀 {result2['skipped']}건")

    # 2. 글 조회
    print("\n=== 글 조회 테스트 ===")
    all_articles = db.get_articles()
    print(f"  전체: {len(all_articles)}건")

    for a in all_articles:
        print(f"  📌 [{a['id']}] {a['title']} - {', '.join(a['tags'])}")

    # 태그 필터
    python_articles = db.get_articles(tag="python")
    print(f"  python 태그: {len(python_articles)}건")

    # 3. 읽음 처리
    print("\n=== 읽음 처리 테스트 ===")
    db.mark_as_read(1)
    read_articles = db.get_articles(is_read=True)
    unread_articles = db.get_articles(is_read=False)
    print(f"  읽음: {len(read_articles)}건, 안 읽음: {len(unread_articles)}건")

    # 4. 북마크
    print("\n=== 북마크 테스트 ===")
    state = db.toggle_bookmark(1)
    print(f"  글 #1 북마크: {state}")
    state = db.toggle_bookmark(1)
    print(f"  글 #1 북마크 해제: {state}")

    # 5. 읽은 글 벡터 조회
    print("\n=== 읽은 글 벡터 조회 ===")
    read_vectors = db.get_read_embeddings()
    if read_vectors is not None:
        print(f"  벡터 shape: {read_vectors.shape}")
    else:
        print("  읽은 글 벡터 없음")

    # 6. 관심 태그
    print("\n=== 관심 태그 테스트 ===")
    db.set_interest_tags(["python", "fastapi", "ai", "backend"])
    tags = db.get_interest_tags()
    print(f"  관심 태그: {[t['tag'] for t in tags]}")

    # 7. 통계
    print("\n=== 통계 ===")
    stats = db.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # 정리
    os.remove(TEST_DB)
    print("\n✅ 테스트 완료 (테스트 DB 삭제됨)")


if __name__ == "__main__":
    main()