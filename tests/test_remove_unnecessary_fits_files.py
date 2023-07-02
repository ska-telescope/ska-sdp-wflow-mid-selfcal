import tempfile
from pathlib import Path

from ska_sdp_wflow_mid_selfcal.cleanup import remove_unnecessary_fits_files

WSCLEAN_FITS_QUALIFIERS = ["dirty", "image", "model", "psf", "residual"]


def _generate_file_names_to_keep() -> list[str]:
    names = [f"somename-{qual}.fits" for qual in WSCLEAN_FITS_QUALIFIERS]
    names_mfs = [
        f"somename-MFS-{qual}.fits" for qual in WSCLEAN_FITS_QUALIFIERS
    ]
    return names + names_mfs


def _generate_file_names_to_delete() -> list[str]:
    names = [f"somename-0042-{qual}.fits" for qual in WSCLEAN_FITS_QUALIFIERS]
    names_mfs = [
        f"somename-{qual}-0042-tmp.fits" for qual in WSCLEAN_FITS_QUALIFIERS
    ]
    return names + names_mfs


def _create_files(dir_path: Path, file_names: list[str]) -> list[Path]:
    path_list = []
    for name in file_names:
        path = dir_path / name
        path.touch()
        path_list.append(path)
    return path_list


def test_remove_unnecessary_fits_files():
    """
    Self-explanatory.
    """
    with tempfile.TemporaryDirectory() as tempdir:
        dir_path = Path(tempdir)
        keep = _create_files(dir_path, _generate_file_names_to_keep())
        delete = _create_files(dir_path, _generate_file_names_to_delete())
        remove_unnecessary_fits_files(dir_path)

        assert all(path.is_file() for path in keep)
        assert all(not path.exists() for path in delete)
