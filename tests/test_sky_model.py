# pylint: disable=redefined-outer-name
import os
import tempfile

import pytest

from ska_sdp_wflow_mid_selfcal.skymodel import SkyModel, Source


@pytest.fixture
def example_skymodel_file_path() -> str:
    """
    Path to the skymodel test file.
    """
    thisdir = os.path.dirname(__file__)
    return os.path.join(thisdir, "data", "example.skymodel")


@pytest.fixture
def expected_example_sources() -> list[Source]:
    """
    Expected contents of the test file after parsing.
    """
    source_1 = Source(
        name="s11",
        shape="POINT",
        patch="Patch_1",
        ra_deg=1.0,
        dec_deg=1.0,
        stokes_i=2.0,
        spectral_index=[2.0, 0.0],
        logarithmic_si=False,
        reference_frequency=1420000000.0,
        major_axis_asec=0.0,
        minor_axis_asec=0.0,
        position_angle_deg=0.0,
    )

    source_2 = Source(
        name="s21",
        shape="POINT",
        patch="Patch_2",
        ra_deg=151.0,
        dec_deg=46.0,
        stokes_i=2.0,
        spectral_index=[2.0, 0.0],
        logarithmic_si=False,
        reference_frequency=1420000000.0,
        major_axis_asec=0.0,
        minor_axis_asec=0.0,
        position_angle_deg=0.0,
    )

    source_3 = Source(
        name="s31",
        shape="GAUSSIAN",
        patch="Patch_3",
        ra_deg=301.0,
        dec_deg=-44.0,
        stokes_i=1.0,
        spectral_index=[1.0, 0.0],
        logarithmic_si=False,
        reference_frequency=666666666.0,
        major_axis_asec=0.0,
        minor_axis_asec=0.0,
        position_angle_deg=0.0,
    )
    return [source_1, source_2, source_3]


def test_parsing_sourcedb_skymodel_file(
    example_skymodel_file_path: str, expected_example_sources: list[Source]
):
    """
    Check that the expected list of sources is parsed from the test sky model
    file.
    """
    sources = SkyModel.load_sourcedb(example_skymodel_file_path).sources
    assert sources == expected_example_sources


def test_skymodel_identical_after_saving_to_sourcedb_then_loading(
    expected_example_sources: list[Source],
):
    """
    Save list of sources to sourcedb file, then load it again and check that
    loaded source list is the same as the original.
    """
    original = SkyModel(expected_example_sources)

    with tempfile.TemporaryDirectory() as tempdir:
        fname = os.path.join(tempdir, "test.skymodel")
        original.save_sourcedb(fname)

        loaded = SkyModel.load_sourcedb(fname)
        assert loaded.sources == original.sources
