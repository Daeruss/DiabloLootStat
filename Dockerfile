# Комбинированный образ для платформ с одним контейнером на проект (RelaxDev и т.п.):
# сначала собираем Vue-фронтенд, затем кладём его в Django-образ, который отдаёт
# и статику SPA, и API. Слушает порт из переменной окружения PORT.

# ── 1. Сборка фронтенда ──
FROM node:20-alpine AS frontend
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ .
RUN npm run build

# ── 2. Backend + собранный фронтенд ──
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
# собранный Vue попадает в BASE_DIR/frontend_dist → Django раздаёт его через WhiteNoise
COPY --from=frontend /fe/dist ./frontend_dist

EXPOSE 8000

CMD ["sh", "entrypoint.sh"]
