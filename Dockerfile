# --- сборка Mini App ---
FROM node:20-alpine AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- бот + API ---
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py ./
COPY app/ app/
COPY api/ api/
COPY --from=frontend /build/dist frontend/dist
# Не от root: uid 1000 должен владеть каталогом data (на сервере: chown -R 1000:1000 data)
RUN useradd --uid 1000 --no-create-home app && mkdir -p data && chown app:app data
USER app
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8080/api/health', timeout=4)" || exit 1
CMD ["python", "main.py"]
