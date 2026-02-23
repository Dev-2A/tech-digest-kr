import json
import re
from datetime import datetime, timezone
from pathlib import Path
from time import mktime

import feedparser
import httpx

from src.collectors.models import FeedEntry


class RSSCollector:
    """RSS 피드를 수집하여 FeedEntry 리스트로 반환"""
    
    def __init__(self, feeds_path: str | None = None):
        if feeds_path is None:
            feeds_path = str(
                Path(__file__).resolve().parent.parent.parent / "config" / "feeds.json"
            )
        self.feeds_path = feeds_path
        self.feeds_config = self._load_feeds_config()
    
    def _load_feeds_config(self) -> list[dict]:
        with open(self.feeds_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [feed for feed in data["feeds"] if feed.get("enabled", True)]
    
    def _clean_html(self, raw_html: str) -> str:
        """HTML 태그를 제거하고 텍스트만 추출"""
        clean = re.sub(r"<[^>]+>", "", raw_html)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean
    
    def _parse_published(self, entry) -> datetime:
        """발행일을 datetime으로 파싱"""
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            return datetime.fromtimestamp(
                mktime(entry.published_parsed), tz=timezone.utc
            )
        if hasattr(entry, "updated_parsed") and entry.updated_parsed:
            return datetime.fromtimestamp(
                mktime(entry.updated_parsed), tz=timezone.utc
            )
        return datetime.now(tz=timezone.utc)
    
    def _extract_tags(self, entry) -> list[str]:
        """RSS 엔트리에서 태그/카테고리 추출"""
        tags = []
        if hasattr(entry, "tags"):
            for tag in entry.tags:
                term = tag.get("term", "").strip().lower()
                if term:
                    tags.append(term)
        return tags
    
    def _extract_content(self, entry) -> str:
        """본문 추출 (content > summary > description 우선순위)"""
        if hasattr(entry, "content") and entry.content:
            raw = entry.content[0].get("value", "")
        elif hasattr(entry, "summary") and entry.summary:
            raw = entry.summary
        elif hasattr(entry, "description") and entry.description:
            raw = entry.description
        else:
            raw = ""
        return self._clean_html(raw)
    
    def collect_feed(self, feed_config: dict) -> list[FeedEntry]:
        """단일 피드에서 글 목록 수집"""
        entries = []
        try:
            response = httpx.get(feed_config["url"], timeout=15, follow_redirects=True)
            parsed = feedparser.parse(response.text)
            
            for entry in parsed.entries:
                feed_entry = FeedEntry(
                    title=entry.get("title", "제목 없음"),
                    url=entry.get("link", ""),
                    author=entry.get("author", "알 수 없음"),
                    published=self._parse_published(entry),
                    content=self._extract_content(entry),
                    platform=feed_config["platform"],
                    feed_name=feed_config["name"],
                    tags=self._extract_tags(entry),
                )
                entries.append(feed_entry)
            
            print(f"  ✅ {feed_config['name']}: {len(entries)}건 수집")
        
        except Exception as e:
            print(f"  ❌ {feed_config['name']}: 수집 실패 - {e}")
        
        return entries
    
    def collect_all(self) -> list[FeedEntry]:
        """등록된 모든 피드에서 글 수집"""
        all_entries = []
        print(f"📡 {len(self.feeds_config)}개 피드 수집 시작...")
        
        for feed_config in self.feeds_config:
            entries = self.collect_feed(feed_config)
            all_entries.extend(entries)
        
        print(f"📦 총 {len(all_entries)}건 수집 완료")
        return all_entries