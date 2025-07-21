import os
from pathlib import Path

__all__ = ["ROOT_PATH", "MAX_FILE_SIZE_MB"]



ROOT_PATH = Path(__file__).resolve().parent.parent.parent.parent
MAX_FILE_SIZE_MB = 50
