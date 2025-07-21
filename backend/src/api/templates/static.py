from litestar.static_files import create_static_files_router

from src.core.config.constants import ROOT_PATH



static_files = create_static_files_router(
    path="/static",
    directories=[ROOT_PATH / "static"]
)
