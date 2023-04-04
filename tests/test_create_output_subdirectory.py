import os
import pathlib
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
        path_str = create_pipeline_output_subdirectory(tempdir_name)
        path = pathlib.Path(path_str)
        assert path.is_dir()
        assert re.match(r"selfcal_\d{8}_\d{6}_\d{6}", path.name)


def test_subdir_creation_raises_if_base_directory_does_not_exist():
    """
    Test that an exception is raised when the base_directory argument to
    create_pipeline_output_subdirectory() does not exist on disk.
    """
    with tempfile.TemporaryDirectory() as tempdir_name:
        non_existent_dir = os.path.join(tempdir_name, "non_existent")
        with pytest.raises(FileNotFoundError):
            create_pipeline_output_subdirectory(non_existent_dir)
