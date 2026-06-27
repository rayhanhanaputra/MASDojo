FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first for layer caching.
COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install .

COPY app ./app

EXPOSE 8000

# The compose command runs init_db + seeder before uvicorn; this CMD is the
# default for running the image standalone.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
