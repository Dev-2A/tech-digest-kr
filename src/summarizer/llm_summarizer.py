from openai import OpenAI

from config.settings import settings


SUMMARY_SYSTEM_PROMPT="""당신은 한국어 기술 블로그 글을 요약하는 전문가입니다.
주어진 글을 정확히 3줄로 요약해주세요.

규칙:
1. 반드시 3줄로 요약합니다. 각 줄은 한 문장입니다.
2. 첫 번째 줄: 글의 핵심 주제 (이 글은 무엇에 대한 글인가)
3. 두 번째 줄: 핵심 내용 또는 방법론 (어떤 내용을 다루는가)
4. 세 번째 줄: 결론 또는 인사이트 (무엇을 얻을 수 있는가)
5. 기술 용어는 원문 그대로 유지합니다.
6. 각 줄은 줄바꿈(\\n)으로 구분합니다.
"""


class LLMSummarizer:
    """OpenAI API를 사용한 블로그 글 3줄 요약기"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
    
    def summarize(self, title: str, content: str) -> dict:
        """
        단일 글을 3줄 요약
        
        Returns:
            {
                "summary": "줄1\\n줄2\\n줄3",
                "lines": ["줄1", "줄2", "줄3"],
                "success": True
            }
        """
        try:
            user_prompt = f"## 제목\n{title}\n\n## 본문\n{content[:3000]}"
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=settings.summary_max_tokens,
                temperature=0.3,
            )
            
            summary_text = response.choices[0].message.content.strip()
            lines = [line.strip() for line in summary_text.split("\n") if line.strip()]
            
            return {
                "summary": "\n".join(lines[:3]),
                "lines": lines[:3],
                "success": True,
            }
        
        except Exception as e:
            print(f"  ❌ 요약 실패 [{title[:30]}...]: {e}")
            return{
                "summary": "",
                "lines": [],
                "success": False,
            }
    
    def summarize_batch(self, entries: list) -> list[dict]:
        """
        FeedEntry 리스트를 일괄 요약
        
        Returns:
            [{"entry": FeedEntry, "summary": dict}, ...]
        """
        results = []
        total = len(entries)
        
        print(f"🤖 {total}건 요약 시작...")
        
        for i, entry in enumerate(entries, 1):
            print(f"  [{i}/{total}] {entry.title[:40]}...")
            summary = self.summarize(entry.title, entry.content)
            results.append({
                "entry": entry,
                "summary": summary,
            })
        
        success_count = sum(1 for r in results if r["summary"]["success"])
        print(f"✅ 요약 완료: {success_count}/{total}건 성공")
        
        return results