import os
import logging
from colorama import init

from core.const import BASE_DIR

LOG_FILE_PATH = os.path.join(BASE_DIR, "..", "latest.log")
CRASH_LOG_FILE_PATH = os.path.join(BASE_DIR, "..", "crash.log")


def setup_logging(crash=False):
    """
    Configures logging to both file and console.
    Returns the logger object.
    """
    logging.basicConfig(
        filename=CRASH_LOG_FILE_PATH if crash else LOG_FILE_PATH,
        filemode="w",
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    logging.getLogger().addHandler(console_handler)

    # Initialize colorama for colored output
    init(autoreset=True)

    return logging.getLogger(__name__)
