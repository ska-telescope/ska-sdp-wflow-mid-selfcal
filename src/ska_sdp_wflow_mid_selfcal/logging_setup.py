import logging
import sys


def setup_logging(logfile_path: str) -> None:
    """
    Configure the root logger to print to stderr and to save all logs to the
    given file path.
    """
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)

    fmt = "[%(levelname)s - %(asctime)s - %(name)s] %(message)s"
    formatter = logging.Formatter(fmt)

    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)
    log.addHandler(stream_handler)

    file_handler = logging.FileHandler(logfile_path)
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)
