FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN useradd -m -u 1000 app
WORKDIR /app

COPY packages.txt .
RUN pip install --upgrade pip && pip install -r packages.txt

COPY --chown=app:app . .
USER app

# Hugging Face Spaces routes traffic to 7860.
EXPOSE 7860
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
