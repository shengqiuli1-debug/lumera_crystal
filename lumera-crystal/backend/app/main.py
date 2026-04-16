import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s:%(name)s:%(message)s",
    )
    for name in [
        "app.services.support_chat_service",
        "app.services.langchain_house_agent",
        "app.tools.house_search_tool",
        "app.tools.house_price_tool",
    ]:
        logging.getLogger(name).setLevel(logging.INFO)


def create_app() -> FastAPI:
    _configure_logging()
    app = FastAPI(title=settings.app_name, version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
