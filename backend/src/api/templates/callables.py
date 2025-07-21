import os
from datetime import datetime, timezone

from src.core.config.constants import ROOT_PATH



def static_version(file_path: str) -> str:
    """
    Devuelve la ruta del archivo con versión hash basada en fecha de modificación.
    """
    full_path = ROOT_PATH / "static" / file_path.lstrip("/")

    if full_path.exists():
        modified_time = os.path.getmtime(full_path)
        version = datetime.fromtimestamp(modified_time, tz=timezone.utc).strftime('%Y%m%d%H%M%S')
        return f"static/{file_path}?v={version}"

    return f"static/{file_path}"




