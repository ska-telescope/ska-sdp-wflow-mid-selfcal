import logging
import os
from typing import Optional, Iterator, Sequence

# TODO: Move type aliases to somewhere sensible
CommandLine = list[str]

# TODO: Also, put that somewhere centralised
log = logging.getLogger("mid-selfcal")


def wsclean_command(
    input_ms: str,
    *,
    temp_dir: str,
    name: str,
    niter: int,
    auto_threshold: float = 3.0,
    mgain: float = 0.8,
    extra_args: Optional[list[str]] = None,
) -> CommandLine:
    """
    Generate a WSCLEAN command-line.
    """
    if extra_args is None:
        extra_args = []

    # TODO: think about where to validate this
    if "-name" in extra_args:
        raise ValueError(
            "-name must not be specified in wsclean extra arguments"
        )

    arg_list = [
        "wsclean",
        "-niter",
        niter,
        "-auto-threshold",
        auto_threshold,
        "-mgain",
        mgain,
        "-name",
        name,
        "-temp-dir",
        temp_dir,
        *extra_args,
        input_ms,
    ]
    return [str(arg) for arg in arg_list]


def dp3_gaincal_command(msin: str, msout: str, *, caltype: str) -> CommandLine:
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
        "gaincal.usemodelcolumn=true",
        "gaincal.applysolution=true",
    ]


def command_line_generator(
    input_ms: str,
    *,
    outdir: str,
    clean_iters: Sequence[int] = (20, 100, 500, 500_000),
    phase_only_cycles: Sequence[int] = (0,),
    wsclean_opts: Optional[list[str]] = None,
) -> Iterator[CommandLine]:
    """
    Iterator that generates the correct, bare-metal command lines to perform
    the self-calibration loop.

    The generated command lines contain only *absolute* paths when
    referring to a file or directory. When executed, we want the command
    lines to behave the same regardless of the working directory from
    where they are called. Also, the code that transforms bare-metal command
    into singularity commands needs all paths to be absolute.
    """
    input_ms = os.path.abspath(input_ms)
    outdir = os.path.abspath(outdir)

    num_cycles = len(clean_iters)
    current_input_ms = input_ms
    calibrated_ms = os.path.join(outdir, "calibrated.ms")

    for icycle, niter in enumerate(clean_iters):
        log.info(f"Starting Major Cycle {icycle + 1} / {num_cycles}")
        yield wsclean_command(
            current_input_ms,
            niter=niter,
            temp_dir=outdir,
            name=f"temp{icycle+1:02d}",
            extra_args=wsclean_opts,
        )

        caltype = (
            "diagonalphase" if icycle in phase_only_cycles else "diagonal"
        )
        yield dp3_gaincal_command(
            current_input_ms,
            calibrated_ms,
            caltype=caltype,
        )
        current_input_ms = calibrated_ms

    log.info(f"Making final image")
    yield wsclean_command(
        current_input_ms,
        niter=clean_iters[-1],
        temp_dir=outdir,
        name="final",
        extra_args=wsclean_opts,
    )
