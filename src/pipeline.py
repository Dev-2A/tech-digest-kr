"""수집 → 요약 → 태그 추출 → 임베딩 → 분류 → 저장 통합 파이프라인"""
from datetime import datetime, timezone

from src.collectors.rss_collector import RSSCollector
from src.summarizer.llm_summarizer import LLMSummarizer
from src.tagger.tag_extractor import TagExtractor, TagFilter
from src.embeddings.embedding_service import EmbeddingService, ArticleClassifier
from src.storage.database import Database
from config.settings import settings


class DigestPipeline:
    """Tech Digest KR 전체 파이프라인"""

    def __init__(self, db: Database | None = None):
        self.db = db or Database()
        self.collector = RSSCollector()
        self.summarizer = LLMSummarizer()
        self.tag_extractor = TagExtractor()
        self.embedding_service = EmbeddingService()
        self.classifier = ArticleClassifier(self.embedding_service)

    def run(self, skip_existing: bool = True) -> dict:
        """
        전체 파이프라인 실행

        Args:
            skip_existing: True면 이미 DB에 있는 글은 건너뜀

        Returns:
            {
                "collected": int,
                "new_articles": int,
                "skipped": int,
                "summarized": int,
                "familiar": int,
                "novel": int,
                "digest": list[dict]
            }
        """
        result = {
            "collected": 0,
            "new_articles": 0,
            "skipped": 0,
            "summarized": 0,
            "familiar": 0,
            "novel": 0,
            "digest": [],
        }

        # === 1단계: RSS 수집 ===
        print("\n" + "=" * 60)
        print("📡 [1/5] RSS 피드 수집")
        print("=" * 60)

        entries = self.collector.collect_all()
        result["collected"] = len(entries)

        if not entries:
            print("⚠️ 수집된 글이 없습니다. 파이프라인을 종료합니다.")
            return result

        # 중복 필터링
        if skip_existing:
            new_entries = [e for e in entries if not self.db.article_exists(e.url)]
            result["skipped"] = len(entries) - len(new_entries)
            entries = new_entries
            print(f"  🆕 신규: {len(entries)}건 | ⏭️ 건너뜀: {result['skipped']}건")

        if not entries:
            print("✅ 새로운 글이 없습니다.")
            return result

        result["new_articles"] = len(entries)

        # === 2단계: LLM 요약 ===
        print("\n" + "=" * 60)
        print("🤖 [2/5] LLM 3줄 요약 생성")
        print("=" * 60)

        summarized = self.summarizer.summarize_batch(entries)
        result["summarized"] = sum(1 for s in summarized if s["summary"]["success"])

        # === 3단계: 태그 추출 ===
        print("\n" + "=" * 60)
        print("🏷️ [3/5] 태그 추출")
        print("=" * 60)

        articles = []
        for item in summarized:
            entry = item["entry"]
            print(f"  [{entry.title[:40]}...]")

            tags = self.tag_extractor.extract_tags(
                entry.title, entry.content, entry.tags
            )
            print(f"    → {', '.join(tags)}")

            articles.append({
                "entry": entry,
                "summary": item["summary"],
                "tags": tags,
            })

        # === 4단계: 임베딩 + 분류 ===
        print("\n" + "=" * 60)
        print("🧠 [4/5] 임베딩 생성 + 읽은 글 기반 분류")
        print("=" * 60)

        # 임베딩 생성
        texts_for_embedding = []
        for article in articles:
            entry = article["entry"]
            summary_text = article["summary"].get("summary", "")
            tag_text = ", ".join(article["tags"])
            texts_for_embedding.append(f"{entry.title} 태그: {tag_text} {summary_text}")

        vectors = self.embedding_service.encode_batch(texts_for_embedding)

        # 읽은 기록 로드 + 분류
        read_vectors = self.db.get_read_embeddings()
        if read_vectors is not None:
            self.classifier.update_read_history(read_vectors)
            print(f"  📚 읽은 글 {len(read_vectors)}건의 벡터를 로드했습니다.")
        else:
            print("  ℹ️ 읽은 기록이 없습니다. 모든 글을 '새로운 글'로 분류합니다.")

        classified = self.classifier.classify(articles)
        result["familiar"] = len(classified["familiar"])
        result["novel"] = len(classified["novel"])

        print(f"  🔄 비슷한 글: {result['familiar']}건")
        print(f"  🆕 새로운 글: {result['novel']}건")

        # === 5단계: DB 저장 ===
        print("\n" + "=" * 60)
        print("💾 [5/5] 데이터베이스 저장")
        print("=" * 60)

        articles_to_save = []
        for i, article in enumerate(articles):
            entry = article["entry"]
            summary = article["summary"]

            articles_to_save.append({
                "url": entry.url,
                "title": entry.title,
                "author": entry.author,
                "published_at": entry.published.isoformat(),
                "content": entry.content_preview,
                "platform": entry.platform,
                "feed_name": entry.feed_name,
                "tags": article["tags"],
                "summary": summary.get("summary", ""),
                "summary_lines": summary.get("lines", []),
                "embedding": vectors[i],
            })

        save_result = self.db.insert_articles_batch(articles_to_save)
        print(f"  ✅ 저장: {save_result['inserted']}건 | ⏭️ 건너뜀: {save_result['skipped']}건")

        # 다이제스트 기록
        self.db.log_digest(
            article_count=len(articles),
            familiar_count=result["familiar"],
            novel_count=result["novel"],
        )

        # === 관심 태그 필터링 결과 ===
        interest_tags_db = self.db.get_interest_tags()
        if interest_tags_db:
            interest_tag_list = [t["tag"] for t in interest_tags_db]
        else:
            interest_tag_list = settings.default_interest_tags

        tag_filter = TagFilter(interest_tags=interest_tag_list)

        # 다이제스트 생성
        digest = []
        for category, label in [("novel", "🆕 새로운 글"), ("familiar", "🔄 비슷한 글")]:
            for item in classified[category]:
                article = item["article"]
                entry = article["entry"]
                relevance = tag_filter.calculate_relevance(article["tags"])

                digest.append({
                    "title": entry.title,
                    "url": entry.url,
                    "author": entry.author,
                    "platform": entry.platform,
                    "tags": article["tags"],
                    "summary_lines": article["summary"].get("lines", []),
                    "category": label,
                    "similarity": item["max_similarity"],
                    "relevance_score": relevance["score"],
                    "matched_tags": relevance["matched_tags"],
                })

        result["digest"] = digest
        return result

    def print_digest(self, result: dict):
        """다이제스트 결과를 보기 좋게 출력"""
        digest = result.get("digest", [])

        if not digest:
            print("\n📭 오늘의 다이제스트가 비어있습니다.")
            return

        print("\n" + "=" * 60)
        print(f"📰 Tech Digest KR — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"   수집 {result['collected']}건 → 신규 {result['new_articles']}건")
        print(f"   🆕 새로운 글 {result['novel']}건 | 🔄 비슷한 글 {result['familiar']}건")
        print("=" * 60)

        current_category = ""
        for item in digest:
            if item["category"] != current_category:
                current_category = item["category"]
                print(f"\n--- {current_category} ---\n")

            print(f"📌 {item['title']}")
            print(f"   👤 {item['author']} | 📦 {item['platform']}")
            print(f"   🏷️ {', '.join(item['tags'])}")

            if item["summary_lines"]:
                print("   📝 요약:")
                for j, line in enumerate(item["summary_lines"], 1):
                    print(f"      {j}. {line}")

            if item["matched_tags"]:
                print(f"   🎯 관심 태그 매칭: {', '.join(item['matched_tags'])}")

            print(f"   🔗 {item['url']}")
            print()