FROM python:3.12-slim

WORKDIR /app

# Build context is the repository root, so the fixtures can be copied into the image
COPY cia-be/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY cia-be/app ./app
COPY fixtures /fixtures

ENV FIXTURES_DIR=/fixtures

EXPOSE 8000
# Render sets PORT, locally the default 8000 is used
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
