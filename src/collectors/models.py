from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FeedEntry:
    """RSS 피드에서 수집한 단일 글"""
    title: str
    url: str
    author: str
    published: datetime
    content: str
    platform: str
    feed_name: str
    tags: list[str] = field(default_factory=list)
    
    @property
    def content_preview(self) -> str:
        """요약용 본문 미리보기 (최대 2000자)"""
        return self.content[:2000] if self.content else ""