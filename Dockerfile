FROM python:3.11-slim


WORKDIR /app
ADD app /app


ENV TZ=America/Sao_Paulo

RUN pip install -r requirements.txt

CMD ["python", "server.py"]
