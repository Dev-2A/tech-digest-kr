"""태그 추출 + 필터링 수동 테스트"""
from src.collectors.rss_collector import RSSCollector
from src.summarizer.llm_summarizer import LLMSummarizer
from src.tagger.tag_extractor import TagExtractor, TagFilter


def main():
    # 1. RSS 수집 (3건만)
    collector = RSSCollector()
    entries = collector.collect_all()[:3]

    if not entries:
        print("❌ 수집된 글이 없습니다.")
        return

    # 2. 요약
    summarizer = LLMSummarizer()
    summarized = summarizer.summarize_batch(entries)

    # 3. 태그 추출
    extractor = TagExtractor()
    print(f"\n🏷️ 태그 추출 시작...")

    articles = []
    for item in summarized:
        entry = item["entry"]
        print(f"  [{entry.title[:40]}...]")
        tags = extractor.extract_tags(entry.title, entry.content, entry.tags)
        print(f"    → {', '.join(tags)}")

        articles.append({
            "entry": entry,
            "summary": item["summary"],
            "tags": tags,
        })

    # 4. 관심 태그 필터링
    tag_filter = TagFilter(interest_tags=["python", "fastapi", "ai", "backend"])
    relevant = tag_filter.filter_relevant(articles)

    print(f"\n{'='*60}")
    print(f"🎯 관심 태그 필터링 결과: {len(relevant)}/{len(articles)}건 관련")
    print(f"{'='*60}\n")

    for r in relevant:
        entry = r["entry"]
        rel = r["relevance"]
        print(f"📌 {entry.title}")
        print(f"   🏷️ 태그: {', '.join(r['tags'])}")
        print(f"   🎯 매칭: {', '.join(rel['matched_tags'])} (점수: {rel['score']})")
        print()


if __name__ == "__main__":
    main()