# Build context must be `services/` so the shared `common/` package is visible:
#   docker build -f services/employee/Dockerfile services/
FROM python:3.11-slim

WORKDIR /app

COPY employee/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY common ./common
COPY employee/app ./app
COPY employee/wsgi.py ./wsgi.py

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

EXPOSE 5001

# The service is stateless (Mongo/Redis hold all state), so it is scaled to
# 3 replicas by Kubernetes; each replica also runs a small worker pool.
CMD ["gunicorn", "-b", "0.0.0.0:5001", "--workers", "2", "wsgi:app"]
