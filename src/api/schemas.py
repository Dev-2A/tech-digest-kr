from pydantic import BaseModel


class ArticleResponse(BaseModel):
    id: int
    url: str
    title: str
    author: str
    published_at: str
    platform: str
    feed_name: str
    tags: list[str]
    summary: str
    summary_lines: list[str]
    is_read: int
    is_bookmarked: int
    created_at: str


class DigestArticle(BaseModel):
    title: str
    url: str
    author: str
    platform: str
    tags: list[str]
    summary_lines: list[str]
    category: str
    similarity: float
    relevance_score: float
    matched_tags: list[str]


class DigestResponse(BaseModel):
    generated_at: str
    collected: int
    new_articles: int
    skipped: int
    familiar: int
    novel: int
    digest: list[DigestArticle]


class StatsResponse(BaseModel):
    total_articles: int
    read_articles: int
    unread_articles: int
    bookmarked_articles: int
    total_digests: int


class InterestTagsRequest(BaseModel):
    tags: list[str]


class MessageResponse(BaseModel):
    message: str
    detail: str = ""