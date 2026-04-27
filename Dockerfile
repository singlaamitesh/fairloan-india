FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY .streamlit/ ./.streamlit/

# Pre-train the model at build time so the first request doesn't pay the
# training cost. Cached in the image layer.
RUN python -m src.train

EXPOSE 8080

CMD ["streamlit", "run", "src/app.py", "--server.port=8080", "--server.address=0.0.0.0"]
