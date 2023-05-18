import pathlib
import shutil

from .logging_setup import LOGGER
from .selfcal_logic import TEMPORARY_MS


def cleanup(directory: str) -> None:
    """
    Delete any temporary files and subdirs created by a pipeline run in the
    given directory.
    """
    LOGGER.info(f"Running cleanup in directory: {directory!r}")
    dir_path = pathlib.Path(directory).absolute().resolve()
    _remove_files_with_suffix(dir_path, ".tmp")
    _remove_directory(dir_path / TEMPORARY_MS)


def remove_non_mfs_fits_if_multi_node_run(directory: str) -> None:
    """
    When running wsclean-mp, remove all FITS files whose name do not contain
    "MFS"; wsclean-mp writes a set of FITS file for every frequency band before
    doing multi-frequency synthesis (MFS).
    This is to avoid using massive amounts of disk space.
    """
    dir_path = pathlib.Path(directory).absolute().resolve()
    condition = any(
        "-MFS-" in path.name and path.is_file() for path in dir_path.iterdir()
    )
    if not condition:
        return

    for path in dir_path.iterdir():
        remove = (
            path.suffix == ".fits"
            and "-MFS-" not in path.name
            and path.is_file()
        )
        if remove:
            path.unlink()
            LOGGER.debug(f"Deleted file: {path}")


def _remove_files_with_suffix(parent_dir: pathlib.Path, suffix: str):
    for path in parent_dir.iterdir():
        if path.suffix == suffix and path.is_file():
            path.unlink()
            LOGGER.debug(f"Deleted file: {path}")


def _remove_directory(directory: pathlib.Path):
    if directory.is_dir():
        shutil.rmtree(str(directory))
        LOGGER.debug(f"Deleted directory: {directory}")
