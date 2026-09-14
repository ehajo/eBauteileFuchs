FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Runtime dependencies deliberately remain separate from development tools.
COPY requirements.lock ./
RUN python -m pip install --no-cache-dir -r requirements.lock

COPY pyproject.toml README.md LICENSE TRADEMARKS.md alembic.ini ./
COPY migrations ./migrations
COPY src ./src
RUN python -m pip install --no-cache-dir --no-deps --no-build-isolation .


FROM base AS production

ENV EBAUTEILEFUCHS_APP_ENV=production \
    EBAUTEILEFUCHS_DATA_DIR=/data \
    EBAUTEILEFUCHS_HOST=0.0.0.0 \
    EBAUTEILEFUCHS_PORT=8008

RUN addgroup --system ebauteilefuchs \
    && adduser --system --ingroup ebauteilefuchs ebauteilefuchs \
    && mkdir -p /data \
    && chown -R ebauteilefuchs:ebauteilefuchs /app /data

COPY packaging/docker/entrypoint.sh /usr/local/bin/ebauteilefuchs-start
RUN chmod 755 /usr/local/bin/ebauteilefuchs-start

USER ebauteilefuchs
EXPOSE 8008
VOLUME ["/data"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD ["python", "-c", "import os, urllib.request; port = os.environ.get('EBAUTEILEFUCHS_PORT', '8008'); urllib.request.urlopen(f'http://127.0.0.1:{port}/api/v1/health', timeout=3)"]

ENTRYPOINT ["/usr/local/bin/ebauteilefuchs-start"]


FROM base AS test

ENV EBAUTEILEFUCHS_APP_ENV=test \
    EBAUTEILEFUCHS_DATA_DIR=/tmp/ebauteilefuchs

COPY requirements-dev.lock ./
RUN python -m pip install --no-cache-dir -r requirements-dev.lock

# Repository-Vertragstests prüfen Dokumentation, freigegebene Branding-Assets und
# die Docker-Konfiguration. Das Testziel erhält deshalb den bereinigten gesamten
# Build-Kontext; Production kopiert diese Dateien weiterhin nicht.
COPY . .

# Docker stellt seine Steuerdateien nicht für COPY aus dem Build-Kontext bereit.
# Diese bytegleichen Testkopien machen die realen Dateien für Vertragstests unter
# ihren erwarteten Pfaden verfügbar.
COPY packaging/docker/test-repository-context/Dockerfile /app/Dockerfile
COPY packaging/docker/test-repository-context/dockerignore /app/.dockerignore

CMD ["pytest"]
