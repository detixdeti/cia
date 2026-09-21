FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Quelltexte kommen im Betrieb per Bind-Mount (siehe docker-compose.yml). Die
# Kopie hier haelt das Image auch ohne Mount lauffaehig.
COPY pyproject.toml ./
COPY src ./src

ENV PYTHONPATH=/app/src

EXPOSE 8000
CMD ["uvicorn", "cia.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
