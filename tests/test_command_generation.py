from dataclasses import dataclass
from pathlib import Path

import pytest

from ska_sdp_wflow_mid_selfcal.command_utils import (
    Command,
    DP3Command,
    WSCleanCommand,
)
from ska_sdp_wflow_mid_selfcal.pipeline import (
    command_generator,
    dp3_merge_command,
)


def test_dp3_merge_command():
    """
    Self-explanatory.
    """
    input_ms_list = [Path("/input/data01.ms"), Path("/input/data02.ms")]
    msout = Path("/output/merged.ms")
    expected_cmd = DP3Command(
        {"msin": input_ms_list, "msout": msout, "steps": []}
    )
    assert dp3_merge_command(input_ms_list, msout) == expected_cmd


@dataclass
class Scenario:
    """
    Convenience class to encapsulate a command-line generation test scenario.
    """

    name: str
    """ Name of the test scenario, shown in the output of pytest -v """

    input_args: dict
    """ Dictionary of input arguments to command_line_generator() """

    expected_commands: list[Command]
    """ Expected command lines, each given as a single string """


# A scenario without any self-calibration cycles, just making the final image
# directly. This can be done by specifying "clean_iters" as an empty sequence.
IMAGE_ONLY_INPUT_ARGS = {
    "input_ms": Path("/input/data.ms"),
    "outdir": Path("/output/dir"),
    "size": (8192, 4096),
    "scale": "1asec",
    "gaincal_solint": 3,
    "gaincal_nchan": 5,
    "clean_iters": (),
    "final_clean_iters": 666_666,
    "phase_only_cycles": (0,),
}

IMAGE_ONLY_EXPECTED_COMMANDS = [
    # Just one imaging step
    WSCleanCommand(
        measurement_sets=[Path("/input/data.ms")],
        flags=[],
        options={
            "-size": (8192, 4096),
            "-scale": "1asec",
            "-niter": 666_666,
            "-weight": "uniform",
            "-gridder": "wgridder",
            "-auto-threshold": 3.0,
            "-mgain": 0.8,
            "-parallel-deconvolution": 2048,
            "-temp-dir": Path("/output/dir"),
            "-name": Path("/output/dir/final"),
        },
    )
]

IMAGE_ONLY = Scenario(
    name="image only",
    input_args=IMAGE_ONLY_INPUT_ARGS,
    expected_commands=IMAGE_ONLY_EXPECTED_COMMANDS,
)


# Single selfcal cycle with phase calibration only, plus final imaging step
ONE_CYCLE_INPUT_ARGS = {
    "input_ms": Path("/input/data.ms"),
    "outdir": Path("/output/dir"),
    "size": (8192, 4096),
    "scale": "1asec",
    "weight": ["briggs", -0.5],
    "gaincal_solint": 3,
    "gaincal_nchan": 5,
    "clean_iters": (100,),
    "phase_only_cycles": (0,),
}

ONE_CYCLE_EXPECTED_COMMANDS = [
    # cycle 1 imaging
    WSCleanCommand(
        measurement_sets=[Path("/input/data.ms")],
        flags=[],
        options={
            "-size": (8192, 4096),
            "-scale": "1asec",
            "-niter": 100,
            "-weight": ["briggs", -0.5],
            "-gridder": "wgridder",
            "-auto-threshold": 3.0,
            "-mgain": 0.8,
            "-parallel-deconvolution": 2048,
            "-temp-dir": Path("/output/dir"),
            "-name": Path("/output/dir/temp01"),
        },
    ),
    # phase-only gaincal
    DP3Command(
        {
            "numthreads": 16,
            "msin": Path("/input/data.ms"),
            "msout": Path("/input/data.ms"),
            "msout.overwrite": True,
            "steps": ["gaincal"],
            "gaincal.caltype": "diagonalphase",
            "gaincal.maxiter": 50,
            "gaincal.solint": 3,
            "gaincal.nchan": 5,
            "gaincal.tolerance": 1e-3,
            "gaincal.usemodelcolumn": True,
            "gaincal.applysolution": True,
        }
    ),
    # final image
    WSCleanCommand(
        measurement_sets=[Path("/input/data.ms")],
        flags=[],
        options={
            "-size": (8192, 4096),
            "-scale": "1asec",
            "-niter": 100_000,
            "-weight": ["briggs", -0.5],
            "-gridder": "wgridder",
            "-auto-threshold": 3.0,
            "-mgain": 0.8,
            "-parallel-deconvolution": 2048,
            "-temp-dir": Path("/output/dir"),
            "-name": Path("/output/dir/final"),
        },
    ),
]

ONE_CYCLE = Scenario(
    name="one selfcal cycle",
    input_args=ONE_CYCLE_INPUT_ARGS,
    expected_commands=ONE_CYCLE_EXPECTED_COMMANDS,
)


# Initial calibration, single selfcal cycle with phase calibration only,
# plus final imaging step
ONE_CYCLE_WITH_INITIAL_CAL_INPUT_ARGS = {
    "input_ms": Path("/input/data.ms"),
    "outdir": Path("/output/dir"),
    "size": (8192, 4096),
    "scale": "1asec",
    "initial_sky_model": Path("/input/skymodel.db"),
    "gaincal_solint": 3,
    "gaincal_nchan": 5,
    "clean_iters": (100,),
    "phase_only_cycles": (0,),
}

ONE_CYCLE_WITH_INITIAL_CAL_EXPECTED_COMMAND_LINES = [
    # Initial gaincal
    DP3Command(
        {
            "numthreads": 16,
            "msin": Path("/input/data.ms"),
            "msout": Path("/input/data.ms"),
            "msout.overwrite": True,
            "steps": ["gaincal"],
            "gaincal.sourcedb": Path("/input/skymodel.db"),
            "gaincal.caltype": "diagonal",
            "gaincal.maxiter": 50,
            "gaincal.solint": 3,
            "gaincal.nchan": 5,
            "gaincal.tolerance": 1e-3,
            "gaincal.propagatesolutions": False,
            "gaincal.usebeammodel": True,
            "gaincal.usechannelfreq": True,
            "gaincal.applysolution": True,
        }
    ),
    # cycle 1 imaging
    WSCleanCommand(
        measurement_sets=[Path("/input/data.ms")],
        flags=[],
        options={
            "-size": (8192, 4096),
            "-scale": "1asec",
            "-niter": 100,
            "-weight": "uniform",
            "-gridder": "wgridder",
            "-auto-threshold": 3.0,
            "-mgain": 0.8,
            "-parallel-deconvolution": 2048,
            "-temp-dir": Path("/output/dir"),
            "-name": Path("/output/dir/temp01"),
        },
    ),
    # phase-only gaincal
    DP3Command(
        {
            "numthreads": 16,
            "msin": Path("/input/data.ms"),
            "msout": Path("/input/data.ms"),
            "msout.overwrite": True,
            "steps": ["gaincal"],
            "gaincal.caltype": "diagonalphase",
            "gaincal.maxiter": 50,
            "gaincal.solint": 3,
            "gaincal.nchan": 5,
            "gaincal.tolerance": 1e-3,
            "gaincal.usemodelcolumn": True,
            "gaincal.applysolution": True,
        }
    ),
    # final image
    WSCleanCommand(
        measurement_sets=[Path("/input/data.ms")],
        flags=[],
        options={
            "-size": (8192, 4096),
            "-scale": "1asec",
            "-niter": 100_000,
            "-weight": "uniform",
            "-gridder": "wgridder",
            "-auto-threshold": 3.0,
            "-mgain": 0.8,
            "-parallel-deconvolution": 2048,
            "-temp-dir": Path("/output/dir"),
            "-name": Path("/output/dir/final"),
        },
    ),
]

ONE_CYCLE_WITH_INITIAL_CAL = Scenario(
    name="one selfcal cycle, with initial calibration",
    input_args=ONE_CYCLE_WITH_INITIAL_CAL_INPUT_ARGS,
    expected_commands=ONE_CYCLE_WITH_INITIAL_CAL_EXPECTED_COMMAND_LINES,
)


# Single calibration loop two cycles: first one with only phase calibration,
# second one with phase and amplitude, plus final imaging step.
TWO_CYCLES_INPUT_ARGS = {
    "input_ms": Path("/input/data.ms"),
    "outdir": Path("/output/dir"),
    "size": (8192, 4096),
    "scale": "1asec",
    "gaincal_solint": 3,
    "gaincal_nchan": 5,
    "clean_iters": (100, 200),
    "phase_only_cycles": (0,),
}

TWO_CYCLES_EXPECTED_COMMAND_LINES = [
    # cycle 1 imaging
    WSCleanCommand(
        measurement_sets=[Path("/input/data.ms")],
        flags=[],
        options={
            "-size": (8192, 4096),
            "-scale": "1asec",
            "-niter": 100,
            "-weight": "uniform",
            "-gridder": "wgridder",
            "-auto-threshold": 3.0,
            "-mgain": 0.8,
            "-parallel-deconvolution": 2048,
            "-temp-dir": Path("/output/dir"),
            "-name": Path("/output/dir/temp01"),
        },
    ),
    # phase-only gaincal
    DP3Command(
        {
            "numthreads": 16,
            "msin": Path("/input/data.ms"),
            "msout": Path("/input/data.ms"),
            "msout.overwrite": True,
            "steps": ["gaincal"],
            "gaincal.caltype": "diagonalphase",
            "gaincal.maxiter": 50,
            "gaincal.solint": 3,
            "gaincal.nchan": 5,
            "gaincal.tolerance": 1e-3,
            "gaincal.usemodelcolumn": True,
            "gaincal.applysolution": True,
        }
    ),
    # cycle 2 imaging
    WSCleanCommand(
        measurement_sets=[Path("/input/data.ms")],
        flags=[],
        options={
            "-size": (8192, 4096),
            "-scale": "1asec",
            "-niter": 200,
            "-weight": "uniform",
            "-gridder": "wgridder",
            "-auto-threshold": 3.0,
            "-mgain": 0.8,
            "-parallel-deconvolution": 2048,
            "-temp-dir": Path("/output/dir"),
            "-name": Path("/output/dir/temp02"),
        },
    ),
    # gaincal, both phase and amplitude
    DP3Command(
        {
            "numthreads": 16,
            "msin": Path("/input/data.ms"),
            "msout": Path("/input/data.ms"),
            "msout.overwrite": True,
            "steps": ["gaincal"],
            "gaincal.caltype": "diagonal",
            "gaincal.maxiter": 50,
            "gaincal.solint": 3,
            "gaincal.nchan": 5,
            "gaincal.tolerance": 1e-3,
            "gaincal.usemodelcolumn": True,
            "gaincal.applysolution": True,
        }
    ),
    # final image
    WSCleanCommand(
        measurement_sets=[Path("/input/data.ms")],
        flags=[],
        options={
            "-size": (8192, 4096),
            "-scale": "1asec",
            "-niter": 100_000,
            "-weight": "uniform",
            "-gridder": "wgridder",
            "-auto-threshold": 3.0,
            "-mgain": 0.8,
            "-parallel-deconvolution": 2048,
            "-temp-dir": Path("/output/dir"),
            "-name": Path("/output/dir/final"),
        },
    ),
]

TWO_CYCLES = Scenario(
    name="two selfcal cycles",
    input_args=TWO_CYCLES_INPUT_ARGS,
    expected_commands=TWO_CYCLES_EXPECTED_COMMAND_LINES,
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
    generated = list(command_generator(**scenario.input_args))
    assert generated == scenario.expected_commands
