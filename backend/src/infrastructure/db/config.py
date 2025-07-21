from litestar.plugins.sqlalchemy import SQLAlchemyAsyncConfig

from src.infrastructure.db.models.base import BaseModel



from src.core.config.settings import env_vars

config_db = SQLAlchemyAsyncConfig(
    connection_string=env_vars.url_db,
    create_all=False,
    metadata=BaseModel.metadata,
    session_dependency_key="db",
    engine_dependency_key="db_engine",
    before_send_handler="autocommit"
)

