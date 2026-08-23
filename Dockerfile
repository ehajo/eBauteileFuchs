FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    EBAUTEILEFUCHS_APP_ENV=production \
    EBAUTEILEFUCHS_DATA_DIR=/data \
    EBAUTEILEFUCHS_HOST=0.0.0.0 \
    EBAUTEILEFUCHS_PORT=8008

WORKDIR /app

RUN addgroup --system ebauteilefuchs \
    && adduser --system --ingroup ebauteilefuchs ebauteilefuchs \
    && mkdir -p /data \
    && chown ebauteilefuchs:ebauteilefuchs /data

COPY pyproject.toml requirements.lock README.md LICENSE TRADEMARKS.md alembic.ini ./
COPY migrations ./migrations
COPY src ./src

RUN python -m pip install --no-cache-dir -r requirements.lock \
    && python -m pip install --no-cache-dir --no-deps --no-build-isolation .

USER ebauteilefuchs
EXPOSE 8008
VOLUME ["/data"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8008/api/v1/health', timeout=3)"]

CMD ["sh", "-c", "alembic upgrade head && python -m ebauteilefuchs"]
