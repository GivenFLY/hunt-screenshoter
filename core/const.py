import os
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent


def get_abspath(path, make_dirs=True):
    path = os.path.join(BASE_DIR, path)
    if make_dirs:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def get_abs_screenshots_path(path, make_dirs=True):
    data_path = os.getenv("ROOT_DATA_DIR", "screenshots/")
    return get_abspath(os.path.join(data_path, path), make_dirs)
