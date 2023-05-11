import os
from typing import Final, Iterator, Optional, Sequence

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
    gridder: str = "wgridder",
    auto_threshold: float = 3.0,
    mgain: float = 0.8,
    parallel_deconvolution: int = 2048,
) -> CommandLine:
    """
    Generate a WSCLEAN command-line. The name of the keyword arguments of this
    function correspond *exactly* to the command-line arguments of WSCLEAN.
    """
    opt_list = []

    # We must deal with "size" separately, because the 2-tuple needs to be
    # unpacked into two separate arguments. We can't pass -size as
    # f"{size[0]} {size[1]}", because the shell will pass e.g. "4096 4096" as a
    # single string argument to wsclean instead of two.
    width, height = size
    opt_list.extend(["-size", str(width), str(height)])

    arg_dict = {
        "-temp-dir": temp_dir,
        "-name": name,
        "-niter": niter,
        "-scale": scale,
        "-gridder": gridder,
        "-auto-threshold": auto_threshold,
        "-mgain": mgain,
        "-parallel-deconvolution": parallel_deconvolution,
    }

    for key, value in arg_dict.items():
        opt_list.append(key)
        opt_list.append(str(value))

    return ["wsclean", *opt_list, input_ms]


def dp3_merge_command(input_ms: list[str], msout: str) -> CommandLine:
    """
    Generate a DP3 command to merge multiple measurement sets into one,
    including only the DATA column. We have do this because gaincal cannot
    handle multiple input MSes.
    """
    csv = ",".join(input_ms)
    msin = f"[{csv}]"
    return ["DP3", f"msin={msin}", f"msout={msout}", "steps=[]"]


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
    return [
        "DP3",
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
    return [
        "DP3",
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
    input_ms_list: list[str],
    *,
    outdir: str,
    size: tuple[int, int],
    scale: str,
    initial_sky_model: Optional[str] = None,
    gaincal_solint: int = 1,
    gaincal_nchan: int = 0,
    clean_iters: Sequence[int],
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
    input_ms_list = [os.path.abspath(fname) for fname in input_ms_list]
    outdir = os.path.abspath(outdir)
    temporary_ms = os.path.join(outdir, TEMPORARY_MS)
    if initial_sky_model:
        initial_sky_model = os.path.abspath(initial_sky_model)

    num_cycles = len(clean_iters)

    # Merge all input MSes into one, because DP3's gaincal can only operate on
    # a single input MS. We do this even if there's only one input MS, because
    # that gives us a fresh MS with only the DATA column, and thus run times
    # representative of a production system (where one would have to take the
    # time to create a MODEL_DATA column for example)
    LOGGER.info("Merging input measurement sets into one")
    yield dp3_merge_command(input_ms_list, temporary_ms)

    if initial_sky_model:
        LOGGER.info(
            "Running initial gain calibration using skymodel: "
            f"{initial_sky_model}"
        )
        yield dp3_initial_gaincal_command(
            temporary_ms,
            temporary_ms,
            caltype="diagonal",
            sourcedb=initial_sky_model,
            solint=gaincal_solint,
            nchan=gaincal_nchan,
        )

    for icycle in range(num_cycles):
        LOGGER.info(f"Starting Major Cycle {icycle + 1} / {num_cycles}")

        yield wsclean_command(
            temporary_ms,
            niter=clean_iters[icycle],
            temp_dir=outdir,
            size=size,
            scale=scale,
            name=f"temp{icycle+1:02d}",
        )

        caltype = (
            "diagonalphase" if icycle in phase_only_cycles else "diagonal"
        )
        yield dp3_gaincal_command(
            temporary_ms,
            temporary_ms,
            caltype=caltype,
            solint=gaincal_solint,
            nchan=gaincal_nchan,
        )

    LOGGER.info("Making final image")
    yield wsclean_command(
        temporary_ms,
        niter=1_000_000,
        temp_dir=outdir,
        size=size,
        scale=scale,
        name="final",
    )
