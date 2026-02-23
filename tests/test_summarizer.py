"""LLM 요약기 수동 테스트"""
from src.collectors.rss_collector import RSSCollector
from src.summarizer.llm_summarizer import LLMSummarizer


def main():
    # 1. RSS 수집 (최신 3건만 테스트)
    collector = RSSCollector()
    entries = collector.collect_all()[:3]

    if not entries:
        print("❌ 수집된 글이 없습니다.")
        return

    # 2. 요약
    summarizer = LLMSummarizer()
    results = summarizer.summarize_batch(entries)

    # 3. 결과 출력
    print(f"\n{'='*60}")
    print(f"요약 결과")
    print(f"{'='*60}\n")

    for r in results:
        entry = r["entry"]
        summary = r["summary"]

        print(f"📌 {entry.title}")
        print(f"🔗 {entry.url}")

        if summary["success"]:
            print("📝 3줄 요약:")
            for j, line in enumerate(summary["lines"], 1):
                print(f"   {j}. {line}")
        else:
            print("   ⚠️ 요약 실패")

        print()


if __name__ == "__main__":
    main()