FROM python:3.11-slim
LABEL authors="diana"

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libpq-dev \
    gcc \
    libmagic1 \
    file \
    mime-support \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY .. .

ENV PYTHONUNBUFFERED=1

CMD ["python", "app.py"]

