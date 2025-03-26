FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    && pip install --no-cache-dir --upgrade pip==24.3.1 \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN chmod +x /app/docker.sh