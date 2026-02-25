"""Tech Digest KR 스케줄러 단독 실행 (서버 없이)"""
import signal
import sys

from src.scheduler import DigestScheduler


def main():
    scheduler = DigestScheduler()

    # 매일 오전 7시 실행
    scheduler.start_daily(hour=7, minute=0)

    # 첫 실행: 즉시 한 번 실행
    print("🚀 첫 다이제스트를 즉시 생성합니다...")
    scheduler._run_job()

    # 종료 시그널 처리
    def shutdown(signum, frame):
        print("\n🛑 종료 신호 수신...")
        scheduler.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print("\n💤 스케줄러 대기 중... (Ctrl+C로 종료)")

    # 무한 대기
    try:
        while True:
            signal.pause()
    except AttributeError:
        # Windows에서는 signal.pause()가 없으므로 대체
        import time
        while True:
            time.sleep(60)


if __name__ == "__main__":
    main()