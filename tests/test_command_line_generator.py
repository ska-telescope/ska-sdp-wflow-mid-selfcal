import shlex
from dataclasses import dataclass

import pytest

from ska_sdp_wflow_mid_selfcal.pipeline import (
    command_line_generator,
    dp3_merge_command,
)


def test_dp3_merge_command():
    """
    Self-explanatory.
    """
    input_ms_list = ["/input/data01.ms", "/input/data02.ms"]
    msout = "/output/merged.ms"
    expected_cmd = (
        "DP3 msin=[/input/data01.ms,/input/data02.ms] msout=/output/merged.ms "
        "steps=[]"
    )
    assert dp3_merge_command(input_ms_list, msout) == shlex.split(expected_cmd)


@dataclass
class Scenario:
    """
    Convenience class to encapsulate a command-line generation test scenario.
    """

    name: str
    """ Name of the test scenario, shown in the output of pytest -v """

    input_args: dict
    """ Dictionary of input arguments to command_line_generator() """

    expected_command_lines: list[str]
    """ Expected command lines, each given as a single string """


# A scenario without any self-calibration cycles, just making the final image
# directly. This can be done by specifying "clean_iters" as an empty sequence.
IMAGE_ONLY_INPUT_ARGS = {
    "input_ms": "/input/data.ms",
    "outdir": "/output/dir",
    "size": (8192, 4096),
    "scale": "1asec",
    "gaincal_solint": 3,
    "gaincal_nchan": 5,
    "clean_iters": (),
    "final_clean_iters": 666_666,
    "phase_only_cycles": (0,),
}

IMAGE_ONLY_EXPECTED_COMMAND_LINES = [
    # Just one imaging step
    "wsclean -temp-dir /output/dir -name final -niter 666666 "
    "-size 8192 4096 -scale 1asec -weight uniform -gridder wgridder "
    "-auto-threshold 3.0 -mgain 0.8 -parallel-deconvolution 2048 "
    "/input/data.ms",
]

IMAGE_ONLY = Scenario(
    name="image only",
    input_args=IMAGE_ONLY_INPUT_ARGS,
    expected_command_lines=IMAGE_ONLY_EXPECTED_COMMAND_LINES,
)


# Single selfcal cycle with phase calibration only, plus final imaging step
ONE_CYCLE_INPUT_ARGS = {
    "input_ms": "/input/data.ms",
    "outdir": "/output/dir",
    "size": (8192, 4096),
    "scale": "1asec",
    "weight": "briggs -0.5",
    "gaincal_solint": 3,
    "gaincal_nchan": 5,
    "clean_iters": (100,),
    "phase_only_cycles": (0,),
}

ONE_CYCLE_EXPECTED_COMMAND_LINES = [
    # cycle 1 imaging
    "wsclean -temp-dir /output/dir -name temp01 -niter 100 "
    "-size 8192 4096 -scale 1asec -weight briggs -0.5 -gridder wgridder "
    "-auto-threshold 3.0 -mgain 0.8 -parallel-deconvolution 2048 "
    "/input/data.ms",
    # phase-only gaincal
    "DP3 numthreads=16 msin=/input/data.ms "
    "msout=/input/data.ms msout.overwrite=true "
    "steps=[gaincal] gaincal.caltype=diagonalphase gaincal.maxiter=50 "
    "gaincal.solint=3 gaincal.nchan=5 "
    "gaincal.tolerance=1e-3 gaincal.usemodelcolumn=true "
    "gaincal.applysolution=true",
    # final image
    "wsclean -temp-dir /output/dir -name final -niter 100000 "
    "-size 8192 4096 -scale 1asec -weight briggs -0.5 -gridder wgridder "
    "-auto-threshold 3.0 -mgain 0.8 -parallel-deconvolution 2048 "
    "/input/data.ms",
]

ONE_CYCLE = Scenario(
    name="one selfcal cycle",
    input_args=ONE_CYCLE_INPUT_ARGS,
    expected_command_lines=ONE_CYCLE_EXPECTED_COMMAND_LINES,
)


# Initial calibration, single selfcal cycle with phase calibration only,
# plus final imaging step
ONE_CYCLE_WITH_INITIAL_CAL_INPUT_ARGS = {
    "input_ms": "/input/data.ms",
    "outdir": "/output/dir",
    "size": (8192, 4096),
    "scale": "1asec",
    "initial_sky_model": "/input/skymodel.db",
    "gaincal_solint": 3,
    "gaincal_nchan": 5,
    "clean_iters": (100,),
    "phase_only_cycles": (0,),
}

ONE_CYCLE_WITH_INITIAL_CAL_EXPECTED_COMMAND_LINES = [
    # Initial gaincal
    "DP3  numthreads=16 msin=/input/data.ms "
    "msout=/input/data.ms msout.overwrite=true "
    "steps=[gaincal] gaincal.caltype=diagonal gaincal.maxiter=50 "
    "gaincal.solint=3 gaincal.nchan=5 "
    "gaincal.tolerance=1e-3 "
    "gaincal.propagatesolutions=false gaincal.usebeammodel=true "
    "gaincal.usechannelfreq=true gaincal.applysolution=true "
    "gaincal.sourcedb=/input/skymodel.db ",
    # cycle 1 imaging
    "wsclean -temp-dir /output/dir -name temp01 -niter 100 "
    "-size 8192 4096 -scale 1asec -weight uniform -gridder wgridder "
    "-auto-threshold 3.0 -mgain 0.8 -parallel-deconvolution 2048 "
    "/input/data.ms",
    # phase-only gaincal
    "DP3 numthreads=16 msin=/input/data.ms "
    "msout=/input/data.ms msout.overwrite=true "
    "steps=[gaincal] gaincal.caltype=diagonalphase gaincal.maxiter=50 "
    "gaincal.solint=3 gaincal.nchan=5 "
    "gaincal.tolerance=1e-3 gaincal.usemodelcolumn=true "
    "gaincal.applysolution=true",
    # final image
    "wsclean -temp-dir /output/dir -name final -niter 100000 "
    "-size 8192 4096 -scale 1asec -weight uniform -gridder wgridder "
    "-auto-threshold 3.0 -mgain 0.8 -parallel-deconvolution 2048 "
    "/input/data.ms",
]

ONE_CYCLE_WITH_INITIAL_CAL = Scenario(
    name="one selfcal cycle, with initial calibration",
    input_args=ONE_CYCLE_WITH_INITIAL_CAL_INPUT_ARGS,
    expected_command_lines=ONE_CYCLE_WITH_INITIAL_CAL_EXPECTED_COMMAND_LINES,
)


# Single calibration loop two cycles: first one with only phase calibration,
# second one with phase and amplitude, plus final imaging step.
TWO_CYCLES_INPUT_ARGS = {
    "input_ms": "/input/data.ms",
    "outdir": "/output/dir",
    "size": (8192, 4096),
    "scale": "1asec",
    "gaincal_solint": 3,
    "gaincal_nchan": 5,
    "clean_iters": (100, 200),
    "phase_only_cycles": (0,),
}

TWO_CYCLES_EXPECTED_COMMAND_LINES = [
    # cycle 1 imaging
    "wsclean -temp-dir /output/dir -name temp01 -niter 100 "
    "-size 8192 4096 -scale 1asec -weight uniform -gridder wgridder "
    "-auto-threshold 3.0 -mgain 0.8 -parallel-deconvolution 2048 "
    "/input/data.ms",
    # phase-only gaincal
    "DP3 numthreads=16 msin=/input/data.ms "
    "msout=/input/data.ms msout.overwrite=true "
    "steps=[gaincal] gaincal.caltype=diagonalphase gaincal.maxiter=50 "
    "gaincal.solint=3 gaincal.nchan=5 "
    "gaincal.tolerance=1e-3 gaincal.usemodelcolumn=true "
    "gaincal.applysolution=true",
    # cycle 2 imaging
    "wsclean -temp-dir /output/dir -name temp02 -niter 200 "
    "-size 8192 4096 -scale 1asec -weight uniform -gridder wgridder "
    "-auto-threshold 3.0 -mgain 0.8 -parallel-deconvolution 2048 "
    "/input/data.ms",
    # gaincal, both phase and amplitude
    "DP3 numthreads=16 msin=/input/data.ms "
    "msout=/input/data.ms msout.overwrite=true "
    "steps=[gaincal] gaincal.caltype=diagonal gaincal.maxiter=50 "
    "gaincal.solint=3 gaincal.nchan=5 "
    "gaincal.tolerance=1e-3 gaincal.usemodelcolumn=true "
    "gaincal.applysolution=true",
    # final image
    "wsclean -temp-dir /output/dir -name final -niter 100000 "
    "-size 8192 4096 -scale 1asec -weight uniform -gridder wgridder "
    "-auto-threshold 3.0 -mgain 0.8 -parallel-deconvolution 2048 "
    "/input/data.ms",
]

TWO_CYCLES = Scenario(
    name="two selfcal cycles",
    input_args=TWO_CYCLES_INPUT_ARGS,
    expected_command_lines=TWO_CYCLES_EXPECTED_COMMAND_LINES,
)


SCENARIOS = [
    IMAGE_ONLY,
    ONE_CYCLE,
    ONE_CYCLE_WITH_INITIAL_CAL,
    TWO_CYCLES,
]

SCENARIO_NAMES = [scenario.name for scenario in SCENARIOS]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=SCENARIO_NAMES)
def test_command_line_generator(scenario: Scenario):
    """
    Test every command line generation scenario defined above.
    """
    generated = list(command_line_generator(**scenario.input_args))
    expected = [shlex.split(text) for text in scenario.expected_command_lines]
    assert generated == expected
