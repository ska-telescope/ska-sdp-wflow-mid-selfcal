# pylint: disable=redefined-outer-name
import copy
import os
import tempfile

import pytest

from ska_sdp_wflow_mid_selfcal.skymodel import (
    FluxModel,
    Shape,
    SkyModel,
    Source,
)


@pytest.fixture
def example_skymodel_file_path() -> str:
    """
    Path to the skymodel test file.
    """
    thisdir = os.path.dirname(__file__)
    return os.path.join(thisdir, "data", "example.sourcedb")


@pytest.fixture
def expected_example_sources() -> list[Source]:
    """
    Expected contents of the test file after parsing.
    """
    source_1 = Source(
        name="s11",
        ra_deg=1.0,
        dec_deg=1.0,
        patch="Patch_1",
        shape=Shape(0.0, 0.0, 0.0),
        flux_model=FluxModel(
            stokes_i=2.0,
            reference_frequency_hz=1420000000.0,
            spectral_index=[2.0, 0.0],
            logarithmic_si=False,
        ),
    )

    source_2 = Source(
        name="s21",
        patch="Patch_2",
        ra_deg=151.0,
        dec_deg=46.0,
        shape=Shape(0.0, 0.0, 0.0),
        flux_model=FluxModel(
            stokes_i=2.0,
            reference_frequency_hz=1420000000.0,
            spectral_index=[2.0, 0.0],
            logarithmic_si=False,
        ),
    )

    source_3 = Source(
        name="s31",
        patch="Patch_3",
        ra_deg=301.0,
        dec_deg=-44.0,
        shape=Shape(0.0, 0.0, 0.0),
        flux_model=FluxModel(
            stokes_i=1.0,
            reference_frequency_hz=666666666.0,
            spectral_index=[1.0, 0.0],
            logarithmic_si=False,
        ),
    )
    return [source_1, source_2, source_3]


def test_source_equality_operator():
    """
    Check that the custom equality operator for Sources works as expected. It
    tolerates small differences in RA/Dec that may arise when parsing
    coordinate strings in DD:MM:SS format.
    """
    source = Source(
        name="a",
        patch="Patch_1",
        ra_deg=0.0,
        dec_deg=0.0,
        shape=Shape(0.0, 0.0, 0.0),
        flux_model=FluxModel(
            stokes_i=2.0,
            reference_frequency_hz=1420000000.0,
            spectral_index=[2.0, 0.0],
            logarithmic_si=False,
        ),
    )

    source_copy = copy.deepcopy(source)
    assert source == source_copy

    # Check that RA/Dec within 1e-12 degrees of each other are acceptable
    source_close = copy.deepcopy(source)
    eps = 1.0e-12
    source_close.ra_deg += eps
    source_close.dec_deg -= eps
    assert source == source_close

    # ... but no more than that
    source_not_close = copy.deepcopy(source)
    eps = 1.0e-11
    source_not_close.ra_deg += eps
    source_not_close.dec_deg -= eps
    assert source != source_not_close


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
        fname = os.path.join(tempdir, "test.sourcedb")
        original.save_sourcedb(fname)

        loaded = SkyModel.load_sourcedb(fname)
        assert loaded.sources == original.sources
