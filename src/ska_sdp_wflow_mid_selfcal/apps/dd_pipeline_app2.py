from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

from astropy.coordinates import SkyCoord

from ska_sdp_wflow_mid_selfcal.command_utils import (
    DP3Command,
)
from ska_sdp_wflow_mid_selfcal.pipeline import run_command


@dataclass
class Source:
    pass


@dataclass
class SkyModel:
    sources: list[Source]


@dataclass
class Patch:
    vertices: SkyCoord


@dataclass
class Tesselation:
    patches: list[Patch]


def create_tesselation(sky_model: SkyModel, field: Field) -> Tesselation:
    pass


def save_sourcedb(
    fpath: Path, tesselation: Tesselation, sky_model: SkyModel
) -> None:
    pass


###############################################################################


@dataclass
class Field:
    centre: SkyCoord
    pixel_scale_deg: float
    num_pixels: int


AntennaConstraints = list[list[str]]
"""Defines groups of antennas constrained to have the same calibration
solutions"""
# TODO: We will have to update the command rendering code to deal with lists
# of lists, which it doesn't at the moment.


SourceDB = Path
"""Path to a .sourcedb file containing a sky model and a set
of calibration directions (patch centres)"""


Observation = Path
"""For the moment, just a Path to a MeasurementSet"""


Solutions = Path
"""For the moment, just a Path to a .h5parm file"""

DDESolveMode = Literal["scalarphase", "scalarcomplexgain", "complexgain"]
"""Accepted solve.mode values for DDECal"""


# What parameters do change between selfcal cycles, and what parameters should
# we expose to the user for experimentation ?
# - Solve type: scalarphase or else
# - Antenna constraint: core-constrained or unconstrained
# - Solution interval
# - Solution bandwidth
class Calibration:
    def __init__(
        self,
        *,
        solve_mode: DDESolveMode,
        antenna_constraints: AntennaConstraints,
        solve_solint: int,
        solve_nchan: int,
        override_dp3_options: Optional[dict] = None,
    ) -> None:
        """
        NOTE: later on, we may want to define solutions interval and bandwidth
        in seconds and Hz instead.
        """
        self._dp3_options = {}  # TODO: define some defaults
        if override_dp3_options:
            self._dp3_options.update(override_dp3_options)
        self._dp3_options.update({
            "solve.mode": solve_mode,
            "solve.antennaconstraint": antenna_constraints,
            "solve.solint": solve_solint,
            "solve.nchan": solve_nchan,
        })

    @property
    def sourcedb_fname() -> str:
        pass

    @property
    def output_solutions_fname() -> str:
        pass

    def dp3_command(self, msin: Path) -> DP3Command:
        pass

    def execute(
        self,
        input_obs: Observation,
        tesselation: Tesselation,
        sky_model: SkyModel,
        *,
        workdir: Path
    ) -> tuple[Solutions, SourceDB]:
        save_sourcedb(self.sourcedb_fname, tesselation, sky_model)
        solutions = self.output_solutions_fname
        cmd = self.dp3_command(input_obs)
        run_command(cmd)
        return solutions, self.sourcedb_fname


class Prediction:
    def execute(self) -> Observation:
        pass


def subtract_observations(
    left: Observation, right: Observation, output_filepath: Path
) -> Observation:
    pass


class Image:
    pass


class Imaging:
    def execute(self, obs: Observation) -> Image:
        pass


def selfcal_pipeline_dd(
    input_obs: Observation,
    core_antennas: list[str],
    imaging_field: Field,
    sky_model: SkyModel,
) -> None:
    """
    TODO
    """
    tesselation = create_tesselation(sky_model, imaging_field)

    calibration = Calibration()
    solutions, sourcedb = calibration.execute(
        input_obs, tesselation, sky_model
    )

    prediction = Prediction()
    predicted_obs = prediction.execute()

    subtracted_obs = subtract_observations(
        input_obs, predicted_obs, Path("TODO")
    )

    imaging = Imaging()
    image = imaging.execute(subtracted_obs)

    # TODO: Identify sources
    # TODO: Update sky models
    # ... loop
