import sqlite3
import json
import numpy as np
from datetime import datetime, timezone
from pathlib import Path

from config.settings import settings


class Database:
    """SQLite 기반 글 메타데이터 + 벡터 저장소"""
    
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or settings.db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()
    
    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn
    
    def _init_tables(self):
        """테이블 초기화"""
        conn = self._get_conn()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    author TEXT DEFAULT '',
                    published_at TEXT NOT NULL,
                    content TEXT DEFAULT '',
                    platform TEXT DEFAULT '',
                    feed_name TEXT DEFAULT '',
                    tags TEXT DEFAULT '[]',
                    summary TEXT DEFAULT '',
                    summary_lines TEXT DEFAULT '[]',
                    embedding BLOB,
                    is_read INTEGER DEFAULT 0,
                    is_bookmarked INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                );
                
                CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url);
                CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at);
                CREATE INDEX IF NOT EXISTS idx_articles_is_read ON articles(is_read);
                
                CREATE TABLE IF NOT EXISTS user_interests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tag TEXT UNIQUE NOT NULL,
                    weight REAL DEFAULT 1.0,
                    created_at TEXT DEFAULT (datetime('now'))
                );
                
                CREATE TABLE IF NOT EXISTS digest_history(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    generated_at TEXT NOT NULL,
                    article_count INTEGER DEFAULT 0,
                    familiar_count INTEGER DEFAULT 0,
                    novel_count INTEGER DEFAULT 0
                );
            """)
            conn.commit()
        finally:
            conn.close()
    
    # === Article CRUD ===
    
    def article_exists(self, url: str) -> bool:
        """URL 기준 중복 체크"""
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT 1 FROM articles WHERE url = ?", (url,)
            ).fetchone()
            return row is not None
        finally:
            conn.close()
    
    def insert_article(self, article_data: dict) -> int | None:
        """
        글 저장 (중복 시 무시)
        
        Args:
            article_data: {
                "url", "title", "author", "published_at",
                "content", "platform", "feed_name",
                "tags": list, "summary": str, "summary_lines": list,
                "embedding": np.ndarray | None
            }
        
        Returns:
            저장된 article id 또는 None (중복)
        """
        if self.article_exists(article_data["url"]):
            return None
        
        conn = self._get_conn()
        try:
            embedding_blob = None
            if article_data.get("embedding") is not None:
                embedding_blob = article_data["embedding"].tobytes()
            
            cursor = conn.execute(
                """
                INSERT INTO articles
                    (url, title, author, published_at, content, platform,
                    feed_name, tags, summary, summary_lines, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    article_data["url"],
                    article_data["title"],
                    article_data.get("author", ""),
                    article_data["published_at"],
                    article_data.get("content", ""),
                    article_data.get("platform", ""),
                    article_data.get("feed_name", ""),
                    json.dumps(article_data.get("tags", []), ensure_ascii=False),
                    article_data.get("summary", ""),
                    json.dumps(article_data.get("summary_lines", []), ensure_ascii=False),
                    embedding_blob,
                ),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    def insert_article_batch(self, articles_data: list[dict]) -> dict:
        """
        글 일괄 저장
        
        Returns:
            {"inserted": int, "skipped": int}
        """
        inserted = 0
        skipped = 0
        
        for data in articles_data:
            result = self.insert_article(data)
            if result is not None:
                inserted += 1
            else:
                skipped += 1
        
        return {"inserted": inserted, "skipped": skipped}
    
    def get_articles(
        self,
        limit: int = 50,
        offset: int = 0,
        is_read: bool | None = None,
        tag: str | None = None,
    ) -> list[dict]:
        """글 목록 조회"""
        conn = self._get_conn()
        try:
            query = "SELECT * FROM articles WHERE 1=1"
            params = []
            
            if is_read is not None:
                query += "  AND is_read = ?"
                params.append(1 if is_read else 0)
            
            if tag:
                query += "  AND tags LIKE  ?"
                params.append(f'%"{tag}"%')
            
            query += "  ORDER BY published_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_dict(row) for row in rows]
        finally:
            conn.close()
    
    def get_article_by_id(self, article_id: int) -> dict | None:
        """ID로 글 조회"""
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM articles WHERE id = ?", (article_id,)
            ).fetchone()
            return self._row_to_dict(row) if row else None
        finally:
            conn.close()
    
    def mark_as_read(self, article_id: int):
        """글 읽음 처리"""
        conn = self._get_conn()
        try:
            conn.execute(
                "UPDATE articles SET is_read = 1, updated_at = datetime('now') WHERE id = ?",
                (article_id,),
            )
            conn.commit()
        finally:
            conn.close()
    
    def toggle_bookmark(self, article_id: int) -> bool:
        """북마크 토글, 변경된 상태 반환"""
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT is_bookmarked FROM articles WHERE id = ?", (article_id,)
            ).fetchone()
            if row is None:
                return False
            
            new_state = 0 if row["is_bookmarked"] else 1
            conn.execute(
                "UPDATE articles SET is_bookmarked = ?, updated_at = datetime('now') WHERE id = ?",
                (new_state, article_id),
            )
            conn.commit()
            return bool(new_state)
        finally:
            conn.close()
    
    # === 읽은 글 벡터 조회 (임베딩 분류용) ===
    
    def get_read_embeddings(self) -> np.ndarray | None:
        """읽은 글의 임베딩 벡터 전체 조회"""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT embedding FROM articles WHERE is_read = 1 AND embedding IS NOT NULL"
            ).fetchall()
            
            if not rows:
                return None
            
            vectors = [np.frombuffer(row["embedding"], dtype=np.float32) for row in rows]
            return np.stack(vectors)
        finally:
            conn.close()
    
    # === 관심 태그 관리 ===
    
    def get_interest_tags(self) -> list[dict]:
        """관심 태그 목록 조회"""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT  tag, weight FROM user_interests ORDER BY weight DESC"
            ).fetchall()
            return [{"tag": row["tag"], "weight": row["weight"]} for row in rows]
        finally:
            conn.close()
    
    def set_interest_tags(self, tags: list[str]):
        """관심 태그 설정 (기존 것 초기화 후 재설정)"""
        conn = self._get_conn()
        try:
            conn.execute("DELETE FROM user_interests")
            for tag in tags:
                conn.execute(
                    "INSERT OR IGNORE INTO user_interests (tag) VALUES (?)",
                    (tag.lower(),),
                )
            conn.commit()
        finally:
            conn.close()
    
    # === 다이제스트 기록 ===
    
    def log_digest(self, article_count: int, familiar_count: int, novel_count: int):
        """다이제스트 생성 기록 저장"""
        conn = self._get_conn()
        try:
            conn.execute(
                """
                INSERT INTO digest_history (generated_at, article_count, familiar_count, novel_count)
                VALUES (?, ?, ?, ?)
                """,
                (datetime.now(tz=timezone.utc).isoformat(), article_count, familiar_count, novel_count),
            )
            conn.commit()
        finally:
            conn.close()
    
    # === 통계 ===
    
    def get_stats(self) -> dict:
        """전체 통계 조회"""
        conn = self._get_conn()
        try:
            total = conn.execute("SELECT COUNT(*) as c FROM articles").fetchone()["c"]
            read = conn.execute("SELECT COUNT(*) as c FROM articles WHERE is_read = 1").fetchone()["c"]
            bookmarked = conn.execute("SELECT COUNT(*) as c FROM articles WHERE is_bookmarked = 1").fetchone()["c"]
            digests = conn.execute("SELECT COUNT(*) as c FROM digest_history").fetchone()["c"]

            return {
                "total_articles": total,
                "read_articles": read,
                "unread_articles": total - read,
                "bookmarked_articles": bookmarked,
                "total_digests": digests,
            }
        finally:
            conn.close()
    
    # === 유틸 ===
    
    def _row_to_dict(self, row: sqlite3.Row) -> dict:
        """sqlite3.Row를 dict로 변환"""
        d = dict(row)
        d["tags"] = json.loads(d.get("tags", "[]"))
        d["summary_lines"] = json.loads(d.get("summary_lines", "[]"))
        d.pop("embedding", None) # 벡터는 API 응답에서 제외
        return d