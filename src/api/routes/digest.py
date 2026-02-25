from fastapi import APIRouter, BackgroundTasks

from src.pipeline import DigestPipeline
from src.scheduler import DigestScheduler
from src.storage.database import Database

router = APIRouter(prefix="/api/digest", tags=["Digest"])
db = Database()
scheduler = DigestScheduler(db=db)

# 파이프라인 실행 상태 관리
_pipeline_status = {"running": False, "last_result": None}


def _run_pipeline():
    """백그라운드에서 파이프라인 실행"""
    _pipeline_status["running"] = True
    try:
        pipeline = DigestPipeline(db=db)
        result = pipeline.run()
        _pipeline_status["last_result"] = {
            "collected": result["collected"],
            "new_articles": result["new_articles"],
            "skipped": result["skipped"],
            "summarized": result["summarized"],
            "familiar": result["familiar"],
            "novel": result["novel"],
            "digest": result["digest"],
        }
    except Exception as e:
        _pipeline_status["last_result"] = {"error": str(e)}
    finally:
        _pipeline_status["running"] = False


@router.post("/run")
def run_digest(background_tasks: BackgroundTasks):
    """다이제스트 파이프라인 수동 실행 (백그라운드)"""
    if _pipeline_status["running"]:
        return {"message": "파이프라인이 이미 실행 중입니다.", "status": "running"}

    background_tasks.add_task(_run_pipeline)
    return {"message": "파이프라인 실행을 시작합니다.", "status": "started"}


@router.get("/status")
def get_status():
    """파이프라인 실행 상태 확인"""
    return {
        "running": _pipeline_status["running"],
        "has_result": _pipeline_status["last_result"] is not None,
    }


@router.get("/latest")
def get_latest_digest():
    """최신 다이제스트 결과 조회"""
    if _pipeline_status["last_result"] is None:
        return {"message": "아직 실행된 다이제스트가 없습니다.", "digest": []}
    return _pipeline_status["last_result"]


# === 스케줄러 API ===

@router.post("/scheduler/start")
def start_scheduler(hour: int = 7, minute: int = 0):
    """매일 아침 스케줄러 시작"""
    scheduler.start_daily(hour=hour, minute=minute)
    return {
        "message": f"스케줄러 시작: 매일 {hour:02d}:{minute:02d}",
        "status": scheduler.get_status(),
    }


@router.post("/scheduler/start-interval")
def start_interval_scheduler(hours: int = 6):
    """간격 기반 스케줄러 시작 (테스트용)"""
    scheduler.start_interval(hours=hours)
    return {
        "message": f"스케줄러 시작: {hours}시간 간격",
        "status": scheduler.get_status(),
    }


@router.post("/scheduler/stop")
def stop_scheduler():
    """스케줄러 중지"""
    scheduler.stop()
    return {"message": "스케줄러 중지됨"}


@router.get("/scheduler/status")
def get_scheduler_status():
    """스케줄러 상태 조회"""
    return scheduler.get_status()