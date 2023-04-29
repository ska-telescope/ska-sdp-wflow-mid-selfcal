import pathlib
import shutil

from ska_sdp_wflow_mid_selfcal.logging_setup import LOGGER


def cleanup(directory: str) -> None:
    """
    Delete any temporary files and subdirs created by a pipeline run in the
    given directory.
    """
    LOGGER.info(f"Running cleanup in directory: {directory!r}")
    dir_path = pathlib.Path(directory).absolute().resolve()
    _remove_files_with_suffix(dir_path, ".tmp")
    _remove_directory(dir_path / "calibrated.ms")


def _remove_files_with_suffix(parent_dir: pathlib.Path, suffix: str):
    for path in parent_dir.iterdir():
        if path.suffix == suffix and path.is_file():
            path.unlink()
            LOGGER.debug(f"Deleted file: {path}")


def _remove_directory(directory: pathlib.Path):
    if directory.is_dir():
        shutil.rmtree(str(directory))
        LOGGER.debug(f"Deleted directory: {directory}")
