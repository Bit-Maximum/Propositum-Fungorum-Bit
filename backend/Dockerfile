FROM python:3.13.5-slim

ARG APP_PATH=backend

RUN pip install --upgrade pip \
    && pip install uv

WORKDIR /app

COPY ${APP_PATH}/pyproject.toml /app/pyproject.toml

RUN uv venv --python 3.13.5 .venv

RUN uv venv \
    && uv lock && uv sync

COPY ${APP_PATH} /app

CMD ["uv", "run", "python", "main.py"]