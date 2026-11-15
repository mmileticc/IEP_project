# Build context must be `services/` so the shared `common/` package is visible:
#   docker build -f services/auth/Dockerfile services/
FROM python:3.11-slim

WORKDIR /app

COPY auth/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY common ./common
COPY auth/app ./app
COPY auth/wsgi.py ./wsgi.py

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

EXPOSE 5000

CMD ["gunicorn", "-b", "0.0.0.0:5000", "--workers", "2", "wsgi:app"]
