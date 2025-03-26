#!/bin/bash

alembic upgrade head

celery -A url_shortener.celery_app.celery_app:celery worker &
gunicorn url_shortener.app:app \
    --workers 1 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind=0.0.0.0:8000