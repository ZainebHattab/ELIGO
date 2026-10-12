FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY requirements-dev.txt requirements.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY . .