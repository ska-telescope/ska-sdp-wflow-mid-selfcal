# pylint: disable=redefined-outer-name
from pathlib import Path

import pytest

from ska_sdp_wflow_mid_selfcal.command_utils import (
    DP3Command,
    Mpirun,
    SingularityExec,
    WSCleanCommand,
    render_command,
    render_command_with_modifiers,
)


@pytest.fixture
def wsclean_command() -> WSCleanCommand:
    """
    WSCleanCommand used for testing rendering.
    """
    return WSCleanCommand(
        measurement_sets=[
            Path("/path/to/data1.ms"),
            Path("/path/to/data2.ms"),
        ],
        flags=["-multiscale"],
        options={
            "-name": "final",
            "-niter": 42,
            "-scale": "1asec",
            "-size": (8192, 4096),
            "-weight": ("briggs", -0.5),
        },
    )


def test_wsclean_command_rendering(wsclean_command: WSCleanCommand):
    """
    Test that WSCleanCommand renders as expected.
    """
    expected = [
        "wsclean",
        "-multiscale",
        "-name",
        "final",
        "-niter",
        "42",
        "-scale",
        "1asec",
        "-size",
        "8192",
        "4096",
        "-weight",
        "briggs",
        "-0.5",
        "/path/to/data1.ms",
        "/path/to/data2.ms",
    ]
    assert render_command(wsclean_command) == expected


def test_wsclean_command_rendering_with_singularity_exec(
    wsclean_command: WSCleanCommand,
):
    """
    Test that WSCleanCommand with SingularityExec modifier renders as expected.
    """
    mod = SingularityExec(Path("singularity_image.sif"))
    expected = [
        "singularity",
        "exec",
        "--bind",
        "/path/to:/mnt/path/to",
        "singularity_image.sif",
        "wsclean",
        "-multiscale",
        "-name",
        "final",
        "-niter",
        "42",
        "-scale",
        "1asec",
        "-size",
        "8192",
        "4096",
        "-weight",
        "briggs",
        "-0.5",
        "/mnt/path/to/data1.ms",
        "/mnt/path/to/data2.ms",
    ]
    assert render_command_with_modifiers(wsclean_command, [mod]) == expected


def test_wsclean_command_rendering_with_singularity_exec_and_mpirun(
    wsclean_command: WSCleanCommand,
):
    """
    Test that WSCleanCommand with SingularityExec and Mpirun modifiers
    as expected.
    """
    sing = SingularityExec(Path("singularity_image.sif"))
    mpirun = Mpirun(8)
    expected = [
        "mpirun",
        "-np",
        "8",
        "-npernode",
        "1",
        "singularity",
        "exec",
        "--bind",
        "/path/to:/mnt/path/to",
        "singularity_image.sif",
        "wsclean-mp",
        "-join-channels",
        "-multiscale",
        "-channels-out",
        "8",
        "-deconvolution-channels",
        "1",
        "-fit-spectral-pol",
        "1",
        "-name",
        "final",
        "-niter",
        "42",
        "-scale",
        "1asec",
        "-size",
        "8192",
        "4096",
        "-weight",
        "briggs",
        "-0.5",
        "/mnt/path/to/data1.ms",
        "/mnt/path/to/data2.ms",
    ]
    assert (
        render_command_with_modifiers(wsclean_command, [sing, mpirun])
        == expected
    )
    assert (
        render_command_with_modifiers(wsclean_command, [mpirun, sing])
        == expected
    )


@pytest.fixture
def dp3_command() -> DP3Command:
    """
    DP3Command used for testing rendering.
    """
    options = {
        "msin": [Path("/path/to/input1.ms"), Path("/path/to/input2.ms")],
        "msout": Path("/path/to/output.ms"),
        "steps": ["gaincal"],
        "gaincal.caltype": "scalarphase",
        "gaincal.solint": 50,
        "gaincal.tolerance": 1e-3,
        "gaincal.applysolution": True,
    }
    return DP3Command(options)


def test_dp3_command_rendering(dp3_command: DP3Command):
    """
    Test that DP3Command renders as expected.
    """
    expected = [
        "DP3",
        "gaincal.applysolution=true",
        "gaincal.caltype=scalarphase",
        "gaincal.solint=50",
        "gaincal.tolerance=0.001",
        "msin=[/path/to/input1.ms,/path/to/input2.ms]",
        "msout=/path/to/output.ms",
        "steps=[gaincal]",
    ]
    assert render_command(dp3_command) == expected


def test_dp3_command_rendering_with_singularity_exec(dp3_command: DP3Command):
    """
    Test that DP3Command with SingularityExec modifier renders as expected.
    """
    mod = SingularityExec(Path("singularity_image.sif"))
    expected = [
        "singularity",
        "exec",
        "--bind",
        "/path/to:/mnt/path/to",
        "singularity_image.sif",
        "DP3",
        "gaincal.applysolution=true",
        "gaincal.caltype=scalarphase",
        "gaincal.solint=50",
        "gaincal.tolerance=0.001",
        "msin=[/mnt/path/to/input1.ms,/mnt/path/to/input2.ms]",
        "msout=/mnt/path/to/output.ms",
        "steps=[gaincal]",
    ]
    assert render_command_with_modifiers(dp3_command, [mod]) == expected
