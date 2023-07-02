import os
from typing import Final, Iterator, Optional, Sequence

from .command_utils import DP3Command
from .logging_setup import LOGGER

CommandLine = list[str]

TEMPORARY_MS: Final[str] = "BewareTheBlob.ms"
""" Name of the temporary measurement set file on which self-calibration is
performed in-place. """


# pylint: disable=too-many-locals
def wsclean_command(
    input_ms: str,
    *,
    temp_dir: str,
    name: str,
    niter: int,
    size: tuple[int, int],
    scale: str,
    weight: str = "uniform",
    gridder: str = "wgridder",
    auto_threshold: float = 3.0,
    mgain: float = 0.8,
    parallel_deconvolution: int = 2048,
) -> CommandLine:
    """
    Generate a WSCLEAN command-line. The name of the keyword arguments of this
    function correspond *exactly* to the command-line arguments of WSCLEAN.
    """
    # NOTE: the "size" argument must be unpacked into two separate strings,
    # otherwise it gets passed as a single string e.g.
    # "4096 4096" which WSClean fails to parse. Same thing for "weight" which
    # could be something like "briggs -1.0" and also needs to be split.
    arg_dict = {
        "-temp-dir": temp_dir,
        "-name": name,
        "-niter": niter,
        "-size": [str(dim) for dim in size],
        "-scale": scale,
        "-weight": weight.split(),
        "-gridder": gridder,
        "-auto-threshold": auto_threshold,
        "-mgain": mgain,
        "-parallel-deconvolution": parallel_deconvolution,
    }

    opt_list = []
    for key, value in arg_dict.items():
        opt_list.append(key)
        if isinstance(value, list):
            opt_list.extend(value)
        else:
            opt_list.append(str(value))

    return ["wsclean", *opt_list, input_ms]


def dp3_merge_command(input_ms_list: list[str], msout: str) -> DP3Command:
    """
    Generate a DP3 command to merge multiple measurement sets into one,
    including only the DATA column. We have do this because gaincal cannot
    handle multiple input MSes.
    """
    print(input_ms_list, msout)
    return DP3Command({"msin": input_ms_list, "msout": msout, "steps": []})


def dp3_gaincal_command(
    msin: str,
    msout: str,
    *,
    caltype: str,
    solint: int,
    nchan: int,
) -> CommandLine:
    """
    Generate a DP3 gain calibration command-line.
    """
    # NOTE: DP3 numthreads MUST be capped to a value <= 63. Otherwise, gaincal
    # may hang indefinitely on a machine with 64 cores or more.
    return [
        "DP3",
        "numthreads=16",
        f"msin={msin}",
        f"msout={msout}",
        "msout.overwrite=true",
        "steps=[gaincal]",
        f"gaincal.caltype={caltype}",
        "gaincal.maxiter=50",
        f"gaincal.solint={solint}",
        f"gaincal.nchan={nchan}",
        "gaincal.tolerance=1e-3",
        "gaincal.usemodelcolumn=true",
        "gaincal.applysolution=true",
    ]


def dp3_initial_gaincal_command(
    msin: str,
    msout: str,
    *,
    caltype: str,
    sourcedb: str,
    solint: int,
    nchan: int,
) -> CommandLine:
    """
    Generate a DP3 initial gain calibration command-line. It requires an
    existing skymodel, and does *not* use the model column.
    """
    # NOTE: DP3 numthreads MUST be capped to a value <= 63. Otherwise, gaincal
    # may hang indefinitely on a machine with 64 cores or more.
    return [
        "DP3",
        "numthreads=16",
        f"msin={msin}",
        f"msout={msout}",
        "msout.overwrite=true",
        "steps=[gaincal]",
        f"gaincal.caltype={caltype}",
        "gaincal.maxiter=50",
        f"gaincal.solint={solint}",
        f"gaincal.nchan={nchan}",
        "gaincal.tolerance=1e-3",
        "gaincal.propagatesolutions=false",
        "gaincal.usebeammodel=true",
        "gaincal.usechannelfreq=true",
        "gaincal.applysolution=true",
        f"gaincal.sourcedb={sourcedb}",
    ]


def command_line_generator(
    input_ms: str,
    *,
    outdir: str,
    size: tuple[int, int],
    scale: str,
    weight: str = "uniform",
    initial_sky_model: Optional[str] = None,
    gaincal_solint: int = 1,
    gaincal_nchan: int = 0,
    clean_iters: Sequence[int],
    final_clean_iters: int = 100_000,
    phase_only_cycles: Sequence[int],
) -> Iterator[CommandLine]:
    """
    Iterator that generates the correct, bare-metal command lines to perform
    the self-calibration loop.

    The generated command lines contain only *absolute* paths when
    referring to a file or directory. When executed, we want the command
    lines to behave the same regardless of the working directory from
    where they are called. Also, the code that transforms bare-metal commands
    into singularity commands needs all paths to be absolute.
    """
    input_ms = os.path.abspath(input_ms)
    outdir = os.path.abspath(outdir)

    if initial_sky_model:
        initial_sky_model = os.path.abspath(initial_sky_model)

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
            name=f"temp{icycle+1:02d}",
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
        name="final",
    )
