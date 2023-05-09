import shlex
from dataclasses import dataclass

import pytest

from ska_sdp_wflow_mid_selfcal.pipeline import command_line_generator
from ska_sdp_wflow_mid_selfcal.selfcal_logic import TEMPORARY_MS


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
# directly. This can be done by specifying "clean_iters" as a list/tuple
# containing just one value.
IMAGE_ONLY_INPUT_ARGS = {
    "input_ms_list": ["/input/data.ms"],
    "outdir": "/output/dir",
    "size": (8192, 4096),
    "scale": "1asec",
    "clean_iters": (100,),
    "phase_only_cycles": (0,),
}

IMAGE_ONLY_EXPECTED_COMMAND_LINES = [
    # Merge command
    f"DP3 msin=[/input/data.ms] msout=/output/dir/{TEMPORARY_MS} steps=[]",
    # Just one imaging step
    "wsclean -size 8192 4096 -temp-dir /output/dir "
    "-name final -niter 100 -scale 1asec -gridder wgridder "
    "-auto-threshold 3.0 -mgain 0.8 -parallel-deconvolution 2048 "
    f"/output/dir/{TEMPORARY_MS}",
]

IMAGE_ONLY = Scenario(
    name="image only",
    input_args=IMAGE_ONLY_INPUT_ARGS,
    expected_command_lines=IMAGE_ONLY_EXPECTED_COMMAND_LINES,
)


# Single selfcal cycle with phase calibration only, plus final imaging step
ONE_CYCLE_INPUT_ARGS = {
    "input_ms_list": ["/input/data.ms"],
    "outdir": "/output/dir",
    "size": (8192, 4096),
    "scale": "1asec",
    "clean_iters": (100, 200),
    "phase_only_cycles": (0,),
}

ONE_CYCLE_EXPECTED_COMMAND_LINES = [
    # Merge command
    f"DP3 msin=[/input/data.ms] msout=/output/dir/{TEMPORARY_MS} steps=[]",
    # cycle 1 imaging
    "wsclean -size 8192 4096 -temp-dir /output/dir "
    "-name temp01 -niter 100 -scale 1asec -gridder wgridder "
    "-auto-threshold 3.0 -mgain 0.8 -parallel-deconvolution 2048 "
    f"/output/dir/{TEMPORARY_MS}",
    # phase-only gaincal
    f"DP3 msin=/output/dir/{TEMPORARY_MS} "
    f"msout=/output/dir/{TEMPORARY_MS} msout.overwrite=true "
    "steps=[gaincal] gaincal.caltype=diagonalphase gaincal.maxiter=50 "
    "gaincal.tolerance=1e-3 gaincal.usemodelcolumn=true "
    "gaincal.applysolution=true",
    # final image
    "wsclean -size 8192 4096 "
    "-temp-dir /output/dir -name final -niter 200 -scale 1asec "
    "-gridder wgridder -auto-threshold 3.0 -mgain 0.8 "
    f"-parallel-deconvolution 2048 /output/dir/{TEMPORARY_MS}",
]

ONE_CYCLE = Scenario(
    name="one selfcal cycle",
    input_args=ONE_CYCLE_INPUT_ARGS,
    expected_command_lines=ONE_CYCLE_EXPECTED_COMMAND_LINES,
)


# Single selfcal cycle with phase calibration only, plus final imaging step
ONE_CYCLE_MULTIPLE_MS_INPUT_ARGS = {
    "input_ms_list": ["/input/data01.ms", "/input/data02.ms"],
    "outdir": "/output/dir",
    "size": (8192, 4096),
    "scale": "1asec",
    "clean_iters": (100, 200),
    "phase_only_cycles": (0,),
}

ONE_CYCLE_MULTIPLE_MS_COMMAND_LINES = [
    # Merge command
    f"DP3 msin=[/input/data01.ms,/input/data02.ms] "
    f"msout=/output/dir/{TEMPORARY_MS} steps=[]",
    # cycle 1 imaging
    "wsclean -size 8192 4096 -temp-dir /output/dir "
    "-name temp01 -niter 100 -scale 1asec -gridder wgridder "
    "-auto-threshold 3.0 -mgain 0.8 -parallel-deconvolution 2048 "
    f"/output/dir/{TEMPORARY_MS}",
    # phase-only gaincal
    f"DP3 msin=/output/dir/{TEMPORARY_MS} "
    f"msout=/output/dir/{TEMPORARY_MS} msout.overwrite=true "
    "steps=[gaincal] gaincal.caltype=diagonalphase gaincal.maxiter=50 "
    "gaincal.tolerance=1e-3 gaincal.usemodelcolumn=true "
    "gaincal.applysolution=true",
    # final image
    "wsclean -size 8192 4096 -temp-dir /output/dir "
    "-name final -niter 200 -scale 1asec -gridder wgridder "
    "-auto-threshold 3.0 -mgain 0.8 -parallel-deconvolution 2048 "
    f"/output/dir/{TEMPORARY_MS}",
]

ONE_CYCLE_MULTIPLE_MS = Scenario(
    name="one selfcal cycle, multiple measurement sets",
    input_args=ONE_CYCLE_MULTIPLE_MS_INPUT_ARGS,
    expected_command_lines=ONE_CYCLE_MULTIPLE_MS_COMMAND_LINES,
)


# Single calibration loop two cycles: first one with only phase calibration,
# second one with phase and amplitude, plus final imaging step.
TWO_CYCLES_INPUT_ARGS = {
    "input_ms_list": ["/input/data.ms"],
    "outdir": "/output/dir",
    "size": (8192, 4096),
    "scale": "1asec",
    "clean_iters": (100, 200, 300),
    "phase_only_cycles": (0,),
}

TWO_CYCLES_EXPECTED_COMMAND_LINES = [
    # Merge command
    f"DP3 msin=[/input/data.ms] msout=/output/dir/{TEMPORARY_MS} steps=[]",
    # cycle 1 imaging
    "wsclean -size 8192 4096 -temp-dir /output/dir "
    "-name temp01 -niter 100 -scale 1asec -gridder wgridder "
    "-auto-threshold 3.0 -mgain 0.8 -parallel-deconvolution 2048 "
    f"/output/dir/{TEMPORARY_MS}",
    # phase-only gaincal
    f"DP3 msin=/output/dir/{TEMPORARY_MS} "
    f"msout=/output/dir/{TEMPORARY_MS} msout.overwrite=true "
    "steps=[gaincal] gaincal.caltype=diagonalphase gaincal.maxiter=50 "
    "gaincal.tolerance=1e-3 gaincal.usemodelcolumn=true "
    "gaincal.applysolution=true",
    # cycle 2 imaging
    "wsclean -size 8192 4096 -temp-dir /output/dir "
    "-name temp02 -niter 200 -scale 1asec -gridder wgridder "
    "-auto-threshold 3.0 -mgain 0.8 -parallel-deconvolution 2048 "
    f"/output/dir/{TEMPORARY_MS}",
    # gaincal, both phase and amplitude
    f"DP3 msin=/output/dir/{TEMPORARY_MS} "
    f"msout=/output/dir/{TEMPORARY_MS} msout.overwrite=true "
    "steps=[gaincal] gaincal.caltype=diagonal gaincal.maxiter=50 "
    "gaincal.tolerance=1e-3 gaincal.usemodelcolumn=true "
    "gaincal.applysolution=true",
    # final image
    "wsclean -size 8192 4096 -temp-dir /output/dir "
    "-name final -niter 300 -scale 1asec -gridder wgridder "
    "-auto-threshold 3.0 -mgain 0.8 -parallel-deconvolution 2048 "
    f"/output/dir/{TEMPORARY_MS}",
]

TWO_CYCLES = Scenario(
    name="two selfcal cycles",
    input_args=TWO_CYCLES_INPUT_ARGS,
    expected_command_lines=TWO_CYCLES_EXPECTED_COMMAND_LINES,
)


SCENARIOS = [IMAGE_ONLY, ONE_CYCLE, ONE_CYCLE_MULTIPLE_MS, TWO_CYCLES]

SCENARIO_NAMES = [scenario.name for scenario in SCENARIOS]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=SCENARIO_NAMES)
def test_command_line_generator(scenario: Scenario):
    """
    Test every command line generation scenario defined above.
    """
    generated = list(command_line_generator(**scenario.input_args))
    expected = [shlex.split(text) for text in scenario.expected_command_lines]
    assert generated == expected
