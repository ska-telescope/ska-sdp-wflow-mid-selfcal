import os
import tempfile
import uuid

import pytest

from ska_sdp_wflow_mid_selfcal.change_dir import ChangeDir


def test_changedir():
    """
    Check that ChangeDir does change the working directory then changes back.
    """
    cwd_before = os.getcwd()
    with tempfile.TemporaryDirectory() as tempdir_name:
        with ChangeDir(tempdir_name):
            assert os.getcwd() == tempdir_name
        assert os.getcwd() == cwd_before


def test_changedir_raises_on_nonexistent_directory():
    """
    Check that FileNotFound is raised when using ChangeDir on a path that does
    not exist.
    """
    with pytest.raises(FileNotFoundError):
        with ChangeDir(f"/whatever/{uuid.uuid4()}"):
            pass
