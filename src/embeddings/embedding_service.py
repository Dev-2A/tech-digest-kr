import numpy as np
from sentence_transformers import SentenceTransformer

from config.settings import settings


class EmbeddingService:
    """문장 임베딩 생성 및 유사도 계산"""
    
    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or settings.embedding_model_name
        self._model = None
    
    @property
    def model(self) -> SentenceTransformer:
        """모델 지연 로딩 (첫 호출 시 로드)"""
        if self._model is None:
            print(f"🔄 임베딩 모델 로딩: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            print(f"✅ 모델 로딩 완료 (차원: {self._model.get_sentence_embedding_dimension()})")
        return self._model
    
    @property
    def dimension(self) -> int:
        return self.model.get_sentence_embedding_dimension()
    
    def encode(self, text: str) -> np.ndarray:
        """단일 텍스트를 벡터로 변환"""
        return self.model.encode(text, normalize_embeddings=True)
    
    def encode_batch(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """텍스트 리스트를 일괄 벡터로 변환"""
        return self.model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=batch_size,
            show_progress_bar=len(texts) > 10,
        )
    
    @staticmethod
    def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """코사인 유사도 계산 (정규화된 벡터 기준)"""
        return float(np.dot(vec_a, vec_b))
    
    @staticmethod
    def cosine_similarity_matrix(vectors_a: np.ndarray, vectors_b: np.ndarray) -> np.ndarray:
        """벡터 그룹 간 유사도 행렬 계산"""
        return np.dot(vectors_a, vectors_b.T)


class ArticleClassifier:
    """읽은 글 기반으로 새 글을 '비슷한 글' vs '새로운 글'로 분류"""
    
    def __init__(self, embedding_service: EmbeddingService | None = None):
        self.embnedding_service = embedding_service or EmbeddingService()
        self.read_vectors: np.ndarray | None = None
    
    def update_read_history(self, read_vectors: np.ndarray):
        """읽은 글 벡터 목록 갱신"""
        self.read_vectors = read_vectors
    
    def _make_article_text(self, title: str, tags: list[str], summary: str = "") -> str:
        """임베딩용 텍스트 생성 (제목 + 태그 + 요약)"""
        parts = [title]
        if tags:
            parts.append(f"태그: {', '.join(tags)}")
        if summary:
            parts.append(summary)
        return " ".join(parts)
    
    def classify(
        self,
        articles: list[dict],
        threshold: float | None = None,
    ) -> dict:
        """
        글 목록을 '비슷한 글'과 '새로운 글'로 분류
        
        Args:
            articles: [{"entry": FeedEntry, "summary": dict, "tags": list}, ...]
            threshold: 유사도 임계값 (기본: settings.similarity_threshold)
        
        Returns:
            {
                "familiar": [{"article": dict, "max_similarity": float}, ...],
                "novel": [{"article": dict, "max_similarity": float}, ...],
            }
        """
        threshold = threshold or settings.similarity_threshold
        
        # 읽은 기록이 없으면 전부 '새로운 글'
        if self.read_vectors is None or len(self.read_vectors) == 0:
            print("  ℹ️ 읽은 기록이 없어 모든 글을 '새로운 글'로 분류합니다.")
            return {
                "familiar": [],
                "novel": [{"article": a, "max_similarity": 0.0} for a in articles],
            }
        
        # 새 글 벡터 생성
        new_texts = []
        for article in articles:
            entry = article["entry"]
            summary_text = article.get("summary", {}).get("summary", "")
            tags = article.get("tags", [])
            text = self._make_article_text(entry.title, tags, summary_text)
            new_texts.append(text)
        
        new_vectors = self.embnedding_service.encode_batch(new_texts)
        
        # 유사도 행렬 계산
        sim_matrix = EmbeddingService.cosine_similarity_matrix(new_vectors, self.read_vectors)
        
        # 분류
        familiar = []
        novel = []
        
        for i, article in enumerate(articles):
            max_sim = float(np.max(sim_matrix[i]))
            
            item = {"article": article, "max_similarity": round(max_sim, 4)}
            
            if max_sim >= threshold:
                familiar.append(item)
            else:
                novel.append(item)
        
        # 정렬: familiar는 유사도 높은 순, novel은 유사도 낮은 순
        familiar.sort(key=lambda x: x["max_similarity"], reverse=True)
        novel.sort(key=lambda x: x["max_similarity"])
        
        return {"familiar": familiar, "novel": novel}