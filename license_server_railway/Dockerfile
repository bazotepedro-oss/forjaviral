FROM python:3.11-slim

WORKDIR /app
COPY license_server.py /app/license_server.py
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1
EXPOSE 8080

CMD ["sh","-c","uvicorn license_server:app --host 0.0.0.0 --port ${PORT:-8080}"]
