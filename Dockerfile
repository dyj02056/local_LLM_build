# 1단계: 화면(React) 빌드
FROM node:22-alpine AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

# 2단계: API 서버 + 빌드된 화면
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY pyproject.toml ./
COPY src/ src/
RUN pip install --no-cache-dir .

COPY app/ app/
COPY scripts/build_shop_db.py scripts/
COPY data/korean/questions.json data/korean/
# 한국어 쇼핑몰 DB는 고정 seed로 이미지 안에서 만든다
RUN python scripts/build_shop_db.py
COPY --from=web /web/dist web/dist

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
