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


def create_tesselation(
    sky_model: SkyModel, field: Field, num_patches: int
) -> Tesselation:
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
"""For the moment, just a Path to a MeasurementSet. Later this would become
a collection of MeasurementSets, e.g. one per sector and/or time chunk."""


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
class DDECal:
    """
    Represents a DDECal step with DP3.
    """

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
        self._dp3_options.update(
            {
                "solve.mode": solve_mode,
                "solve.antennaconstraint": antenna_constraints,
                "solve.solint": solve_solint,
                "solve.nchan": solve_nchan,
            }
        )

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
        workdir: Path,
    ) -> tuple[Solutions, SourceDB]:
        sourcedb_path = workdir / self.sourcedb_fname
        save_sourcedb(sourcedb_path, tesselation, sky_model)
        solutions = workdir / self.output_solutions_fname
        cmd = self.dp3_command(input_obs)
        run_command(cmd)
        return solutions, sourcedb_path


# Predict has very few free parameters here, should be simple
class Prediction:
    def execute(
        self, input_obs: Observation, solutions: Solutions
    ) -> Observation:
        pass


def subtract_observations(
    left: Observation, right: Observation, output_filepath: Path
) -> Observation:
    pass


class Imaging:
    def __init__(self) -> None:
        pass

    def execute(self, obs: Observation, field: Field) -> None:
        pass


def selfcal_pipeline_dd(
    input_obs: Observation,
    sky_model: SkyModel,
    image_size: tuple[int, int],
    pixel_scale: str,
    config_dict: dict,
) -> None:
    """
    TODO
    """

    field = Field()

    for cycle_index, cycle_params in enumerate(
        config_dict["selfcal_cycles"], start=1
    ):

        tesselation = create_tesselation(
            sky_model,
            field,
            num_patches=cycle_params["tesselation"]["num_patches"],
        )

        dde_par = cycle_params["ddecal"]
        ddecal = DDECal(
            solve_mode=dde_par["solve_mode"],
            antenna_constraints=dde_par["antenna_constraints"],
            solve_solint=dde_par["solve_solint"],
            solve_nchan=dde_par["solve_nchan"],
            override_dp3_options=dde_par["override_dp3_options"],
        )
        solutions, sourcedb = ddecal.execute(input_obs, tesselation, sky_model)

        prediction = Prediction()
        predicted_obs = prediction.execute()

        subtracted_obs = subtract_observations(
            input_obs, predicted_obs, Path("TODO")
        )

        imaging = Imaging()
        imaging.execute(subtracted_obs)

        # TODO: Identify sources
        # TODO: Update sky models
        # ... loop
