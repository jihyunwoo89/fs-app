FROM python:3.11-slim

WORKDIR /app

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Dart 설치 (필요한 경우)
RUN apt-get update && apt-get install -y wget gnupg
RUN wget -qO- https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/dart.gpg
RUN echo 'deb [signed-by=/usr/share/keyrings/dart.gpg arch=amd64] https://storage.googleapis.com/download.dartlang.org/linux/debian stable main' | tee /etc/apt/sources.list.d/dart_stable.list
RUN apt-get update && apt-get install -y dart

# 애플리케이션 코드 복사
COPY . .

# 포트 설정
EXPOSE 8080

# 애플리케이션 실행
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]