FROM python:3.11-slim

# 메모리 효율성을 위한 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONIOENCODING=utf-8

WORKDIR /app

# 시스템 패키지 업데이트 및 필수 도구만 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사 (선택적으로)
COPY *.py ./
COPY templates/ ./templates/
COPY static/ ./static/
COPY corp_codes_sample.json ./
COPY .env ./ 2>/dev/null || echo ".env 파일이 없습니다 - 환경변수 사용"

# 포트 설정
EXPOSE 8080

# Gunicorn으로 더 안정적인 실행 (메모리 제한 고려)
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "2", "--timeout", "120", "--keep-alive", "2", "--max-requests", "1000", "--max-requests-jitter", "50", "app:app"]