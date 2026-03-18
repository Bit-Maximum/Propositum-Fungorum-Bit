from typing import TYPE_CHECKING
import logging

import uvicorn

from app import create_app, settings

if TYPE_CHECKING:
    from fastapi import FastAPI


logger = logging.getLogger(__name__)


if __name__ == "__main__":
    app: 'FastAPI' = create_app()

    logger.warning("Запуск приложения...")

    uvicorn.run(
        app=app,
        host=settings.APP.HOST,
        port=settings.APP.PORT,
    )
