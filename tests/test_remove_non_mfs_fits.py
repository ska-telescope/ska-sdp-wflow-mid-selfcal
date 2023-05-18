import tempfile
from pathlib import Path

from ska_sdp_wflow_mid_selfcal.cleanup import (
    remove_non_mfs_fits_if_multi_node_run,
)

# Test: removes all fits except MFS fits if any MFS fits are present
# Test: removes nothing if no MFS fits are present

WSCLEAN_FITS_SUFFIXES = [
    "dirty.fits",
    "image.fits",
    "model.fits",
    "psf.fits",
    "residual.fits",
]


def _generate_mfs_fits_names(basename: str) -> list[str]:
    return [f"{basename}-MFS-{suffix}" for suffix in WSCLEAN_FITS_SUFFIXES]


def _generate_non_mfs_fits_names(basename: str) -> list[str]:
    return [f"{basename}-{suffix}" for suffix in WSCLEAN_FITS_SUFFIXES]


def _create_mfs_fits_files(dir_path: Path, basename: str) -> list[Path]:
    path_list = []
    for name in _generate_mfs_fits_names(basename):
        path = dir_path / name
        path.touch()
        path_list.append(path)
    return path_list


def _create_non_mfs_fits_files(dir_path: Path, basename: str) -> list[Path]:
    path_list = []
    for name in _generate_non_mfs_fits_names(basename):
        path = dir_path / name
        path.touch()
        path_list.append(path)
    return path_list


def test_non_mfs_fits_are_removed_if_any_mfs_fits_present():
    """
    Self-explanatory.
    """
    with tempfile.TemporaryDirectory() as tempdir:
        dir_path = Path(tempdir)
        basename = "temp01"
        mfs_fits = _create_mfs_fits_files(dir_path, basename)
        non_mfs_fits = _create_non_mfs_fits_files(dir_path, basename)
        remove_non_mfs_fits_if_multi_node_run(tempdir)

        assert all(path.is_file() for path in mfs_fits)
        assert all(not path.exists() for path in non_mfs_fits)


def test_nothing_is_removed_if_no_mfs_fits_present():
    """
    Self-explanatory.
    """
    with tempfile.TemporaryDirectory() as tempdir:
        dir_path = Path(tempdir)
        basename = "temp01"
        non_mfs_fits = _create_non_mfs_fits_files(dir_path, basename)
        remove_non_mfs_fits_if_multi_node_run(tempdir)

        assert all(path.is_file() for path in non_mfs_fits)
