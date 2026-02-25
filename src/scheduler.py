"""APScheduler 기반 자동 다이제스트 생성 스케줄러"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

from src.pipeline import DigestPipeline
from src.storage.database import Database
from config.settings import settings


class DigestScheduler:
    """매일 아침 자동으로 다이제스트를 생성하는 스케줄러"""

    def __init__(self, db: Database | None = None):
        self.db = db or Database()
        self.scheduler = BackgroundScheduler()
        self._last_run = None
        self._last_result = None

    def _run_job(self):
        """스케줄링된 파이프라인 실행"""
        print(f"\n⏰ [{datetime.now().strftime('%Y-%m-%d %H:%M')}] 스케줄 파이프라인 시작")
        try:
            pipeline = DigestPipeline(db=self.db)
            result = pipeline.run()
            self._last_run = datetime.now()
            self._last_result = {
                "collected": result["collected"],
                "new_articles": result["new_articles"],
                "familiar": result["familiar"],
                "novel": result["novel"],
                "success": True,
            }
            pipeline.print_digest(result)
            print(f"⏰ 스케줄 파이프라인 완료")
        except Exception as e:
            print(f"❌ 스케줄 파이프라인 실패: {e}")
            self._last_run = datetime.now()
            self._last_result = {"success": False, "error": str(e)}

    def start_daily(self, hour: int = 7, minute: int = 0):
        """
        매일 지정 시각에 실행

        Args:
            hour: 실행 시각 (시, 기본 7시)
            minute: 실행 시각 (분, 기본 0분)
        """
        self.scheduler.add_job(
            self._run_job,
            trigger=CronTrigger(hour=hour, minute=minute),
            id="daily_digest",
            name="매일 아침 다이제스트",
            replace_existing=True,
        )
        self.scheduler.start()
        print(f"📅 스케줄러 시작: 매일 {hour:02d}:{minute:02d}에 다이제스트를 생성합니다.")

    def start_interval(self, hours: int | None = None):
        """
        일정 간격으로 실행 (테스트용)

        Args:
            hours: 실행 간격 (시간, 기본: settings.rss_fetch_interval_hours)
        """
        interval = hours or settings.rss_fetch_interval_hours

        self.scheduler.add_job(
            self._run_job,
            trigger=IntervalTrigger(hours=interval),
            id="interval_digest",
            name=f"{interval}시간 간격 다이제스트",
            replace_existing=True,
        )
        self.scheduler.start()
        print(f"🔁 스케줄러 시작: {interval}시간 간격으로 다이제스트를 생성합니다.")

    def stop(self):
        """스케줄러 중지"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("⏹️ 스케줄러 중지됨")

    def get_status(self) -> dict:
        """스케줄러 상태 조회"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time) if job.next_run_time else None,
            })

        return {
            "running": self.scheduler.running,
            "jobs": jobs,
            "last_run": str(self._last_run) if self._last_run else None,
            "last_result": self._last_result,
        }