from pathlib import Path
from typing import Final, Iterator, Optional, Sequence

from .command_utils import Command, DP3Command, WSCleanCommand
from .logging_setup import LOGGER


TEMPORARY_MS: Final[str] = "BewareTheBlob.ms"
""" Name of the temporary measurement set file on which self-calibration is
performed in-place. """


# pylint: disable=too-many-locals
def wsclean_command(
    input_ms: Path,
    *,
    temp_dir: Path,
    name: Path,
    niter: int,
    size: tuple[int, int],
    scale: str,
    weight: list[str] = ["uniform"],
    gridder: str = "wgridder",
    auto_threshold: float = 3.0,
    mgain: float = 0.8,
    parallel_deconvolution: int = 2048,
) -> WSCleanCommand:
    """
    Generate a WSCLEAN command-line. The name of the keyword arguments of this
    function correspond *exactly* to the command-line arguments of WSCLEAN.
    """
    options = {
        "-temp-dir": temp_dir,
        "-name": name,
        "-niter": niter,
        "-size": size,
        "-scale": scale,
        "-weight": weight,
        "-gridder": gridder,
        "-auto-threshold": auto_threshold,
        "-mgain": mgain,
        "-parallel-deconvolution": parallel_deconvolution,
    }
    return WSCleanCommand(
        measurement_sets=[input_ms], flags=[], options=options
    )


def dp3_merge_command(input_ms_list: list[str], msout: str) -> DP3Command:
    """
    Generate a DP3 command to merge multiple measurement sets into one,
    including only the DATA column. We have do this because gaincal cannot
    handle multiple input MSes.
    """
    print(input_ms_list, msout)
    return DP3Command({"msin": input_ms_list, "msout": msout, "steps": []})


def dp3_gaincal_command(
    msin: Path,
    msout: Path,
    *,
    caltype: str,
    solint: int,
    nchan: int,
) -> DP3Command:
    """
    Generate a DP3 gain calibration command-line.
    """
    # NOTE: DP3 numthreads MUST be capped to a value <= 63. Otherwise, gaincal
    # may hang indefinitely on a machine with 64 cores or more.
    return DP3Command(
        {
            "numthreads": 16,
            "msin": msin,
            "msout": msout,
            "msout.overwrite": True,
            "steps": ["gaincal"],
            "gaincal.caltype": caltype,
            "gaincal.maxiter": 50,
            "gaincal.solint": solint,
            "gaincal.nchan": nchan,
            "gaincal.tolerance": 1e-3,
            "gaincal.usemodelcolumn": True,
            "gaincal.applysolution": True,
        }
    )


def dp3_initial_gaincal_command(
    msin: Path,
    msout: Path,
    *,
    caltype: str,
    sourcedb: Path,
    solint: int,
    nchan: int,
) -> DP3Command:
    """
    Generate a DP3 initial gain calibration command-line. It requires an
    existing skymodel, and does *not* use the model column.
    """
    # NOTE: DP3 numthreads MUST be capped to a value <= 63. Otherwise, gaincal
    # may hang indefinitely on a machine with 64 cores or more.
    return DP3Command(
        {
            "numthreads": 16,
            "msin": msin,
            "msout": msout,
            "msout.overwrite": True,
            "steps": ["gaincal"],
            "gaincal.caltype": caltype,
            "gaincal.maxiter": 50,
            "gaincal.solint": solint,
            "gaincal.nchan": nchan,
            "gaincal.tolerance": 1e-3,
            "gaincal.propagatesolutions": False,
            "gaincal.usebeammodel": True,
            "gaincal.usechannelfreq": True,
            "gaincal.applysolution": True,
            "gaincal.sourcedb": sourcedb,
        }
    )


def command_line_generator(
    input_ms: Path,
    *,
    outdir: Path,
    size: tuple[int, int],
    scale: str,
    weight: str = "uniform",
    initial_sky_model: Optional[Path] = None,
    gaincal_solint: int = 1,
    gaincal_nchan: int = 0,
    clean_iters: Sequence[int],
    final_clean_iters: int = 100_000,
    phase_only_cycles: Sequence[int],
) -> Iterator[Command]:
    """
    Iterator that generates the correct, bare-metal command lines to perform
    the self-calibration loop.
    """
    num_cycles = len(clean_iters)

    if initial_sky_model:
        LOGGER.info(
            "Running initial gain calibration using skymodel: "
            f"{initial_sky_model}"
        )
        yield dp3_initial_gaincal_command(
            input_ms,
            input_ms,
            caltype="diagonal",
            sourcedb=initial_sky_model,
            solint=gaincal_solint,
            nchan=gaincal_nchan,
        )

    for icycle in range(num_cycles):
        LOGGER.info(f"Starting Major Cycle {icycle + 1} / {num_cycles}")

        yield wsclean_command(
            input_ms,
            niter=clean_iters[icycle],
            temp_dir=outdir,
            size=size,
            scale=scale,
            weight=weight,
            name=outdir / f"temp{icycle+1:02d}",
        )

        caltype = (
            "diagonalphase" if icycle in phase_only_cycles else "diagonal"
        )
        yield dp3_gaincal_command(
            input_ms,
            input_ms,
            caltype=caltype,
            solint=gaincal_solint,
            nchan=gaincal_nchan,
        )

    LOGGER.info("Making final image")
    yield wsclean_command(
        input_ms,
        niter=final_clean_iters,
        temp_dir=outdir,
        size=size,
        scale=scale,
        weight=weight,
        name=outdir / "final",
    )
