FROM python:3.11-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    cmake \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY causal_analysis/ ./causal_analysis/
COPY *.py ./

EXPOSE 8000

CMD ["uvicorn", "causal_analysis.api.main:app", "--host", "0.0.0.0", "--port", "8000"]