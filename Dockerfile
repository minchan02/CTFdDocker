FROM python:3.9-slim

# Flask와 Docker SDK 설치
RUN pip install flask docker

# 컨테이너의 작업 디렉토리 설정
WORKDIR /app

# Flask 애플리케이션 파일 복사
COPY . .

# Flask 애플리케이션 실행
CMD ["python", "app.py"]
