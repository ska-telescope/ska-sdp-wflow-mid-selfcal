import re
import shutil
from pathlib import Path

from .logging_setup import LOGGER
from .selfcal_logic import TEMPORARY_MS


def cleanup(directory: Path) -> None:
    """
    Delete any temporary files and subdirs created by a pipeline run in the
    given directory.
    """
    LOGGER.info(f"Running cleanup in directory: {directory!r}")
    directory = directory.absolute().resolve()
    _remove_files_with_suffix(directory, ".tmp")
    _remove_directory(directory / TEMPORARY_MS)
    remove_unnecessary_fits_files(directory)


def remove_unnecessary_fits_files(directory: Path) -> None:
    """
    Remove any temporary or intermediate .fits files that wsclean-mp creates
    in multi-node runs. In particular, wsclean-mp writes a set of FITS files
    for every frequency band before doing multi-frequency synthesis (MFS).
    This is to avoid using massive amounts of disk space.
    """
    directory = directory.absolute().resolve()

    patterns = [
        r"(.*?)-(\d{4})-(dirty|image|model|psf|residual).fits",
        r"(.*?)-(dirty|image|model|psf|residual)-(\d{4})-tmp.fits",
    ]

    for path in directory.iterdir():
        if any(re.match(pat, path.name) for pat in patterns):
            path.unlink()
            LOGGER.debug(f"Deleted file: {path}")


def _remove_files_with_suffix(parent_dir: Path, suffix: str):
    for path in parent_dir.iterdir():
        if path.suffix == suffix and path.is_file():
            path.unlink()
            LOGGER.debug(f"Deleted file: {path}")


def _remove_directory(directory: Path):
    if directory.is_dir():
        shutil.rmtree(str(directory))
        LOGGER.debug(f"Deleted directory: {directory}")
