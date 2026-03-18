FROM python:3.13.5-slim

ARG APP_PATH=rec-trimmer

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ${APP_PATH}/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем остальной код приложения
COPY ${APP_PATH} /app


# Запуск приложения
CMD ["python", "main.py"]