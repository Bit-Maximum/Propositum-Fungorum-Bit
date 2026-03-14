from fastapi import FastAPI


def create_app() -> FastAPI:
    app: FastAPI = FastAPI(
        title="Сионистский обрезатель рекомендаций",
        description="Находит фрагменты с хирургическим лечением и вырезает их",
        version="1.0.0",
    )

    return app
