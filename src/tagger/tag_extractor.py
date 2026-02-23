from openai import OpenAI

from config.settings import settings


TAG_SYSTEM_PROMPT = """당신은 한국어 기술 블로그 글의 태그를 추출하는 전문가입니다.

주어진 글의 제목과 본문을 분석하여 기술 태그를 추출해주세요.

규칙:
1. 태그는 영문 소문자로 작성합니다.
2. 최소 2개, 최대 5개의 태그를 추출합니다.
3. 태그는 쉼표(,)로 구분하여 한 줄로 출력합니다.
4. 태그만 출력합니다. 설명이나 부연은 없습니다.
5. 가능한 한 아래 태그 목록에서 선택합니다. 해당하는 것이 없으면 새 태그를 만들어도 됩니다.

태그 목록:
python, javascript, typescript, java, kotlin, go, rust, c, cpp,
react, vue, nextjs, svelte, angular,
fastapi, django, flask, spring, express, nestjs,
docker, kubernetes, cicd, github-actions, terraform,
aws, gcp, azure, cloud, serverless,
ai, ml, llm, nlp, embedding, rag, fine-tuning,
database, postgresql, mysql, mongodb, redis, elasticsearch,
frontend, backend, fullstack, devops, mlops, security,
testing, performance, architecture, microservice, api,
linux, git, vscode, algorithm, data-structure
"""


class TagExtractor:
    """LLM을 사용한 기술 태그 추출기"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
    
    def extract_tags(self, title: str, content: str, existing_tags: list[str] | None = None) -> list[str]:
        """
        글에서 기술 태그를 추출
        
        Args:
            title: 글 제목
            content: 글 본문
            existing_tags: RSS에서 이미 수집된 태그 (참고용)
        
        Returns:
            ["python", "fastapi", "backend"] 형태의 태그 리스트
        """
        try:
            hint = ""
            if existing_tags:
                hint = f"\n\n참고 - RSS에서 수집된 기존 태그: {', '.join(existing_tags)}"
            
            user_prompt = f"## 제목\n{title}\n\n## 본문\n{content[:2000]}{hint}"
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": TAG_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=100,
                temperature=0.1,
            )
            
            raw = response.choices[0].message.content.strip()
            tags = [tag.strip().lower() for tag in raw.split(",") if tag.strip()]
            return tags[:5]
        
        except Exception as e:
            print(f"  ❌ 태그 추출 실패 [{title[:30]}...]: {e}")
            return existing_tags or []


class TagFilter:
    """관심 태그 기반 필터링"""
    
    def __init__(self, interest_tags: list[str] | None = None):
        self.interest_tags = set(
            interest_tags or settings.default_interest_tags
        )
    
    def calculate_relevance(self, article_tags: list[str]) -> dict:
        """
        관심 태그와의 관련도 계산
        
        Returns:
            {
                "score": 0.0 ~ 1.0,
                "matched_tags": ["python", "fastapi"],
                "is_relevant": True/False
            }
        """
        if not article_tags:
            return {"score": 0.0, "matched_tags": [], "is_relevant": False}
        
        article_tag_set = set(article_tags)
        matched = article_tag_set & self.interest_tags
        
        score = len(matched) / len(article_tag_set) if article_tag_set else 0.0
        
        return {
            "score": round(score, 2),
            "matched_tags": sorted(list(matched)),
            "is_relevant": len(matched) > 0,
        }
    
    def filter_relevant(self, articles: list[dict], min_score: float = 0.0) -> list[dict]:
        """
        관심 태그와 관련된 글만 필터링
        매칭 결과가 0건이면 전체 글을 관련도 0으로 반환 (놓치는 글 방지)
        """
        results = []

        for article in articles:
            tags = article.get("tags", [])
            relevance = self.calculate_relevance(tags)

            if relevance["is_relevant"] and relevance["score"] >= min_score:
                article["relevance"] = relevance
                results.append(article)

        # 매칭 결과가 0건이면 전체 글을 낮은 관련도로 포함
        if not results:
            print("  ⚠️ 관심 태그 매칭 결과가 0건이므로 전체 글을 포함합니다.")
            for article in articles:
                article["relevance"] = {
                    "score": 0.0,
                    "matched_tags": [],
                    "is_relevant": False,
                }
                results.append(article)

        results.sort(key=lambda x: x["relevance"]["score"], reverse=True)
        return results