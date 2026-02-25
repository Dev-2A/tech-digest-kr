"""Tech Digest KR 파이프라인 수동 실행"""
from src.pipeline import DigestPipeline


def main():
    pipeline = DigestPipeline()
    result = pipeline.run()
    pipeline.print_digest(result)


if __name__ == "__main__":
    main()