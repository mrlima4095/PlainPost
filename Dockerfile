FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app


ADD app /app


ENV TZ=America/Sao_Paulo

RUN pip install -r requirements.txt

CMD ["python", "server.py"]
