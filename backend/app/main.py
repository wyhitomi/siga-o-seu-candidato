from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.modules import health
from app.modules.parliamentarians.router import senators, state_deputies

API_DESCRIPTION = """
API pública e anônima para pesquisar quem governa o país, a partir de bases
de dados abertas do governo. Rotas em `/api/v1/admin` exigem login de
administrador.
"""


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Siga o seu candidato API",
        version="0.1.0",
        description=API_DESCRIPTION,
        docs_url="/docs",
        redoc_url=None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(health.router)
    app.include_router(senators)
    app.include_router(state_deputies)
    return app


app = create_app()
