from litestar import Litestar
from litestar.plugins.sqlalchemy import SQLAlchemyPlugin

from src.core.config.settings import env_vars
from src.core.config.logging import logging_config
from src.api.routes_v1 import routes
from src.api.templates import template_config, static_files
from src.api.middlewares.auth import AuthMiddleware
from src.infrastructure.db.config import config_db



DEBUG_STATE = env_vars.environment == "dev"


app = Litestar(
    route_handlers=[static_files, *routes],
    template_config=template_config,
    plugins=[
        SQLAlchemyPlugin(config=config_db)
    ],
    debug=DEBUG_STATE,
    logging_config=logging_config,
    middleware=[AuthMiddleware]
)

# uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload