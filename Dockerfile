# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    GARAGEHUB_ENV=production \
    GARAGEHUB_DATA_DIR=/var/data/garagehub \
    PORT=10000

WORKDIR /app
COPY requirements.txt requirements-production.txt ./
# O certificado opcional atende ao proxy do ambiente de desenvolvimento.
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then \
      PIP_CERT=/run/secrets/proxy_ca pip install --no-cache-dir -r requirements-production.txt; \
    else \
      pip install --no-cache-dir -r requirements-production.txt; \
    fi

RUN useradd --create-home --uid 10001 garagehub \
    && mkdir -p /var/data/garagehub \
    && chown -R garagehub:garagehub /var/data
COPY app ./app
COPY run.py seed.py gunicorn.conf.py ./
USER garagehub
EXPOSE 10000
CMD ["gunicorn", "--config", "gunicorn.conf.py", "run:app"]
