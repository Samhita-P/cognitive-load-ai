FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn uvicorn

COPY . .

EXPOSE 8000
CMD ["sh", "-c", "gunicorn core.asgi:application -k uvicorn.workers.UvicornWorker --workers ${WEB_CONCURRENCY:-$(( $(nproc) * 2 + 1 ))} --bind 0.0.0.0:8000"]
