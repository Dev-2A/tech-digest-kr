# 📰 Tech Digest KR

한국어 기술 블로그 RSS를 수집하고, LLM으로 3줄 요약을 생성하여 관심 태그별 개인 뉴스레터를 제공하는 서비스입니다.

## ✨ 주요 기능

- 🔗 **RSS 수집**: velog, tistory 등 한국어 기술 블로그 RSS 자동 수집
- 🤖 **LLM 3줄 요약**: OpenAI API로 글마다 핵심 3줄 요약 생성
- 🏷️ **태그 자동 분류**: LLM이 기술 태그를 추출하고 관심 태그와 매칭
- 🧠 **읽은 글 vs 새 글 분류**: 임베딩 유사도로 "비슷한 글"과 "새로운 글" 구분
- 📬 **개인 뉴스레터 UI**: 매일 아침 읽기 편한 다크 테마 웹 인터페이스
- ⏰ **자동 스케줄링**: 매일 지정 시각에 자동으로 수집 + 요약 + 분류

## 📸 스크린샷

> 서버 실행 후 `http://localhost:8009/app` 에서 확인할 수 있습니다.

## 🛠️ 기술 스택

| 영역 | 기술 |
| ------ | ------ |
| 백엔드 | Python 3.11+, FastAPI, Uvicorn |
| RSS 파싱 | feedparser, httpx |
| LLM 요약/태그 | OpenAI API (gpt-4o-mini) |
| 임베딩 | sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2) |
| 데이터베이스 | SQLite |
| 스케줄러 | APScheduler |
| 프론트엔드 | Vanilla HTML/CSS/JS |

## 📁 프로젝트 구조

```text
tech-digest-kr/
├── run_digest.py          # 파이프라인 수동 실행
├── run_server.py          # API 서버 실행
├── run_scheduler.py       # 스케줄러 단독 실행
├── requirements.txt
├── config/
│   ├── settings.py        # 앱 설정 (Pydantic)
│   └── feeds.json         # RSS 피드 소스 목록
├── src/
│   ├── pipeline.py        # 통합 파이프라인
│   ├── scheduler.py       # 자동 스케줄링
│   ├── collectors/
│   │   ├── models.py      # FeedEntry 데이터 모델
│   │   └── rss_collector.py
│   ├── summarizer/
│   │   └── llm_summarizer.py
│   ├── tagger/
│   │   └── tag_extractor.py
│   ├── embeddings/
│   │   └── embedding_service.py
│   ├── storage/
│   │   └── database.py
│   └── api/
│       ├── app.py         # FastAPI 앱
│       ├── schemas.py
│       ├── routes/
│       │   ├── articles.py
│       │   ├── digest.py
│       │   └── settings.py
│       └── templates/     # 프론트엔드
│           ├── index.html
│           └── static/
├── tests/
│   ├── test_collector.py
│   ├── test_summarizer.py
│   ├── test_tagger.py
│   ├── test_embeddings.py
│   └── test_storage.py
└── data/
    └── digest.db          # (자동 생성)
```

## 🚀 시작하기

### 1. 클론 및 환경 설정

```bash
git clone https://github.com/Dev-2A/tech-digest-kr.git
cd tech-digest-kr
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 환경 변수 설정

```bash
copy .env.example .env
```

`.env` 파일을 열고 OpenAI API 키를 입력합니다:

```env
OPENAI_API_KEY=sk-your-api-key-here
DEBUG=true
```

### 3. RSS 피드 소스 추가 (선택)

`config/feeds.json`을 열어 원하는 블로그 RSS를 추가합니다:

```json
{
  "feeds": [
    {
      "name": "내 블로그",
      "url": "https://myblog.tistory.com/rss",
      "platform": "tistory",
      "enabled": true
    }
  ]
}
```

### 4. 실행

```bash
# 방법 A: 웹 서버 실행 (추천)
python run_server.py
# → http://localhost:8009/app 에서 UI 확인
# → http://localhost:8009/docs 에서 API 문서 확인

# 방법 B: 파이프라인 1회 수동 실행
python run_digest.py

# 방법 C: 스케줄러 단독 실행 (매일 오전 7시 자동)
python run_scheduler.py
```

## 📡 API 엔드포인트

| Method | Endpoint | 설명 |
| -------- | ---------- | ------ |
| GET | `/api/articles` | 글 목록 조회 |
| GET | `/api/articles/{id}` | 글 상세 조회 |
| POST | `/api/articles/{id}/read` | 읽음 처리 |
| POST | `/api/articles/{id}/bookmark` | 북마크 토글 |
| POST | `/api/digest/run` | 파이프라인 수동 실행 |
| GET | `/api/digest/latest` | 최신 다이제스트 조회 |
| GET | `/api/digest/status` | 파이프라인 상태 확인 |
| POST | `/api/digest/scheduler/start` | 스케줄러 시작 |
| POST | `/api/digest/scheduler/stop` | 스케줄러 중지 |
| GET | `/api/settings/tags` | 관심 태그 조회 |
| PUT | `/api/settings/tags` | 관심 태그 수정 |
| GET | `/api/settings/stats` | 통계 조회 |

## ⚙️ 설정

`config/settings.py` 또는 `.env`에서 변경 가능한 주요 설정:

| 환경 변수 | 기본값 | 설명 |
| ----------- | -------- | ------ |
| `OPENAI_API_KEY` | (필수) | OpenAI API 키 |
| `OPENAI_MODEL` | `gpt-4o-mini` | 요약/태그에 사용할 모델 |
| `EMBEDDING_MODEL_NAME` | `paraphrase-multilingual-MiniLM-L12-v2` | 임베딩 모델 |
| `SIMILARITY_THRESHOLD` | `0.75` | 읽은 글 유사도 임계값 |
| `RSS_FETCH_INTERVAL_HOURS` | `6` | 간격 스케줄러 주기 |
| `API_PORT` | `8000` | API 서버 포트 |

## 🔮 향후 계획

- [ ] 이메일 뉴스레터 발송 (SMTP)
- [ ] 더 많은 RSS 소스 기본 제공 (GeekNews, Medium 한국어 등)
- [ ] 태그별 트렌드 시각화 대시보드
- [ ] Docker 컨테이너화
- [ ] 다국어 지원 (영어 기술 블로그)

## 📄 License

MIT License
