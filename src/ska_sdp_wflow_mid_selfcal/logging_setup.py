import logging
import sys
from typing import Final

LOGGER_NAME: Final[str] = "mid-selfcal"
""" Name for the top-level pipeline logger """

LOGGER = logging.getLogger(LOGGER_NAME)
""" Top-level pipeline logger """


def setup_logging(logfile_path: str) -> None:
    """
    Configure the top-level pipeline logger to print to stderr and to save all
    logs to the given file path.
    """
    LOGGER.setLevel(logging.DEBUG)

    fmt = "[%(levelname)s - %(asctime)s - %(name)s] %(message)s"
    formatter = logging.Formatter(fmt)

    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)
    LOGGER.addHandler(stream_handler)

    file_handler = logging.FileHandler(logfile_path)
    file_handler.setFormatter(formatter)
    LOGGER.addHandler(file_handler)
