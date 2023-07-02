import os
from pathlib import Path
import re
import tempfile

import pytest

from ska_sdp_wflow_mid_selfcal.directory_creation import (
    create_pipeline_output_subdirectory,
)


def test_subdir_creation():
    """
    Test the creation of the pipeline output subdirectory.
    """
    with tempfile.TemporaryDirectory() as tempdir_name:
        tempdir_path = Path(tempdir_name)
        creatd_path = create_pipeline_output_subdirectory(tempdir_path)
        assert creatd_path.is_dir()
        assert re.match(r"selfcal_\d{8}_\d{6}_\d{6}", creatd_path.name)


def test_subdir_creation_raises_if_base_directory_does_not_exist():
    """
    Test that an exception is raised when the base_directory argument to
    create_pipeline_output_subdirectory() does not exist on disk.
    """
    with tempfile.TemporaryDirectory() as tempdir_name:
        tempdir_path = Path(tempdir_name)
        non_existent_dir = tempdir_path / "non_existent"
        with pytest.raises(FileNotFoundError):
            create_pipeline_output_subdirectory(non_existent_dir)
