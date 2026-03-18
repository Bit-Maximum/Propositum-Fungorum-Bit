from fastapi import FastAPI

from .api.routes import healthcheck_router, trimmer_router


def create_app() -> FastAPI:
    app: FastAPI = FastAPI(
        title="Сионистский обрезатель рекомендаций",
        description="Находит фрагменты с хирургическим лечением и вырезает их",
        version="1.0.0",
    )

    app.include_router(healthcheck_router)
    app.include_router(trimmer_router)

    return app
