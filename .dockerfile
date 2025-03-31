FROM python:3.10-alpine

RUN apk update && apk add --no-cache gcc musl-dev postgresql-dev git

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt psycopg2-binary

COPY . /app/

CMD ["gunicorn", "ai_photo_bot.asgi:application", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "2"]

