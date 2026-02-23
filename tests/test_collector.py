"""RSS 수집기 수동 테스트"""
from src.collectors.rss_collector import RSSCollector


def main():
    collector = RSSCollector()
    entries = collector.collect_all()

    print(f"\n{'='*60}")
    print(f"수집 결과: 총 {len(entries)}건")
    print(f"{'='*60}\n")

    for i, entry in enumerate(entries[:5], 1):
        print(f"[{i}] {entry.title}")
        print(f"    👤 {entry.author} | 📅 {entry.published.strftime('%Y-%m-%d %H:%M')}")
        print(f"    🔗 {entry.url}")
        print(f"    🏷️ {', '.join(entry.tags) if entry.tags else '태그 없음'}")
        print(f"    📝 {entry.content_preview[:100]}...")
        print()


if __name__ == "__main__":
    main()