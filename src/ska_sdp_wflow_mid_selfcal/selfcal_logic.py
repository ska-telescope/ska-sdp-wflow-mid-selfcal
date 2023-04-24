import logging
import os
from typing import Iterator, Sequence

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
    size: tuple[int, int],
    scale: str,
    clean_iters: Sequence[int] = (20, 100, 500, 500_000),
    phase_only_cycles: Sequence[int] = (0,),
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

    num_cycles = len(clean_iters)
    current_input_ms = input_ms
    calibrated_ms = os.path.join(outdir, "calibrated.ms")

    for icycle, niter in enumerate(clean_iters):
        log.info(f"Starting Major Cycle {icycle + 1} / {num_cycles}")
        yield wsclean_command(
            current_input_ms,
            niter=niter,
            temp_dir=outdir,
            size=size,
            scale=scale,
            name=f"temp{icycle+1:02d}",
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
        size=size,
        scale=scale,
        name="final",
    )
