from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

from astropy.coordinates import SkyCoord
import astropy.units as u

from ska_sdp_wflow_mid_selfcal.command_utils import DP3Command, WSCleanCommand
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

    def save_ds9_file(self, fpath: Path) -> None:
        pass


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
    pixel_scale_asec: float
    num_pixels: int


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
        input_obs: Observation,
        sourcedb: SourceDB,
        output_solutions: Solutions,
        *,
        solve_mode: DDESolveMode,
        solve_solint: int,
        solve_nchan: int,
        override_dp3_options: Optional[dict] = None,
    ) -> None:
        """
        NOTE: later on, we may want to define solutions interval and bandwidth
        in seconds and Hz instead.
        Also, we may want to add antenna constraints.
        """
        self._input_obs = input_obs
        self._sourcedb = sourcedb
        self._output_solutions = output_solutions

        self._dp3_options = {}  # TODO: define some defaults
        if override_dp3_options:
            self._dp3_options.update(override_dp3_options)
        self._dp3_options.update(
            {
                "solve.mode": solve_mode,
                "solve.solint": solve_solint,
                "solve.nchan": solve_nchan,
            }
        )

    def get_command(self) -> DP3Command:
        pass  # TODO

    @classmethod
    def from_config_dict(
        cls,
        input_obs: Observation,
        sourcedb: SourceDB,
        output_solutions: Solutions,
        conf: dict,
    ) -> DDECal:
        return cls(
            input_obs,
            sourcedb,
            output_solutions,
            solve_mode=conf["solve_mode"],
            solve_solint=conf["solve_solint"],
            solve_nchan=conf["solve_nchan"],
            override_dp3_options=conf["override_dp3_options"],
        )


class Imaging:
    def __init__(
        self,
        input_obs: Observation,
        field: Field,
        solutions: Solutions,
        *,
        override_wsclean_options: Optional[dict] = None,
    ) -> None:
        pass

    def get_command(self) -> WSCleanCommand:
        pass

    @classmethod
    def from_config_dict(
        cls,
        input_obs: Observation,
        field: Field,
        solutions: Solutions,
        conf: dict,
    ) -> Imaging:
        return cls(input_obs, field, solutions)  # TODO


def selfcal_pipeline_dd(
    input_obs: Observation,
    sky_model: SkyModel,
    *,
    num_pixels: int,
    pixel_scale_asec: float,
    config_dict: dict,
    outdir: Path,
) -> None:
    """
    Inputs to this function are already parsed.
    """

    field = Field(
        centre=SkyCoord(0.0, 0.0, unit=(u.deg, u.deg)),  # TODO
        pixel_scale_asec=pixel_scale_asec,
        num_pixels=num_pixels,
    )

    for cycle_index, cycle_params in enumerate(
        config_dict["selfcal_cycles"], start=1
    ):

        tesselation = create_tesselation(
            sky_model,
            field,
            num_patches=cycle_params["tesselation"]["num_patches"],
        )

        sourcedb = outdir / "skymodel.sourcedb"
        save_sourcedb(sourcedb, tesselation, sky_model)

        solutions = outdir / "solutions.h5parm"

        ddecal = DDECal.from_config_dict(
            input_obs, sourcedb, solutions, cycle_params["ddecal"]
        )
        dp3_command = ddecal.get_command()
        # run_command(dp3_command)

        imaging = Imaging.from_config_dict(input_obs, field, solutions, cycle_params["imaging"])
        wsclean_command = imaging.get_command()
        # run_command(wsclean_command)

        # TODO: Identify sources
        # TODO: Update sky models
