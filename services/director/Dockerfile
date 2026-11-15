# Build context must be `services/` so the shared `common/` package is visible:
#   docker build -f services/director/Dockerfile services/
FROM python:3.11-slim

WORKDIR /app

COPY director/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Voting.sol is not compiled here: app/contracts/Voting.compiled.json already
# holds the ABI and bytecode, so the image needs no solc and no network.
COPY common ./common
COPY director/app ./app
COPY director/wsgi.py ./wsgi.py

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

EXPOSE 5002

# One worker process so the background voting listener (app/listener.py)
# runs exactly once; threads keep request concurrency.
CMD ["gunicorn", "-b", "0.0.0.0:5002", "--workers", "1", "--threads", "4", "wsgi:app"]
