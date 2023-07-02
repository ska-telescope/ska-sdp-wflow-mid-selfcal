import tempfile
from pathlib import Path

from ska_sdp_wflow_mid_selfcal.cleanup import cleanup
from ska_sdp_wflow_mid_selfcal.selfcal_logic import TEMPORARY_MS


def test_cleanup():
    """
    Test that the expected files are removed when calling cleanup().
    """
    with tempfile.TemporaryDirectory() as tempdir:
        tempdir_path = Path(tempdir)

        # Create .tmp file
        tmp_file = tempdir_path / "file.tmp"
        tmp_file.touch()

        # Create mock calibrated measurement set directory containing one
        # subdir and one file
        calibrated_ms = tempdir_path / TEMPORARY_MS
        calibrated_ms.mkdir()
        (calibrated_ms / "subdir").mkdir()
        (calibrated_ms / "somefile").touch()

        cleanup(tempdir_path)
        assert not tmp_file.exists()
        assert not calibrated_ms.exists()


def test_cleanup_empty_directory():
    """
    Check that no exceptions are raised when some or all of the files to be
    deleted are missing.
    """
    with tempfile.TemporaryDirectory() as tempdir:
        cleanup(Path(tempdir))
