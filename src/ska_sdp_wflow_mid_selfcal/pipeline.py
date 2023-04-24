import logging
import signal
import subprocess
import time

from typing import Sequence

from ska_sdp_wflow_mid_selfcal.change_dir import ChangeDir
from ska_sdp_wflow_mid_selfcal.singularify import CommandLine, singularify
from ska_sdp_wflow_mid_selfcal.selfcal_logic import command_line_generator

log = logging.getLogger("mid-selfcal")


def selfcal_pipeline(
    input_ms: str,
    *,
    outdir: str,
    singularity_image: str,
    size: tuple[int, int],
    scale: str,
    clean_iters: Sequence[int] = (20, 100, 500, 500_000),
    phase_only_cycles: Sequence[int] = (0,),
) -> None:
    """
    Run the direction-independent self-calibration pipeline.

    Args:
        input_ms: path to the input Measurement Set as a string
        outdir: path to the directory where all output files will be written
        singularity_image: path to the singularity image file with both wsclean
            and DP3 installed.
        size: size of the output image in pixels as an int tuple
            (width, height).
        scale: scale of a pixel, as a string such as "20asec" or "0.01deg".
        clean_iters: maximum Clean iterations per self-cal cycle. The number of
            calibration cycles is one less than the length of the list, as the
            final value is used to make the image after the last calibration.
        phase_only_cycles: sequence of self-cal cycle indices (zero-based) in
            which to perform phase-only calibration.
    """
    setup_exit_handler()
    try:
        generator = command_line_generator(
            input_ms,
            outdir=outdir,
            size=size,
            scale=scale,
            clean_iters=clean_iters,
            phase_only_cycles=phase_only_cycles,
        )
        for cmd in generator:
            singularity_cmd = singularify(cmd, singularity_image)
            run_command_line_in_workdir(singularity_cmd, outdir)
        log.info("Pipeline run: SUCCESS")

    # pylint: disable=broad-exception-caught
    except (Exception, SystemExit) as err:
        log.exception(f"Error: {err!r}")
        log.error("Pipeline run: FAIL")

    finally:
        # This will run even if SystemExit is raised by the exit handler
        cleanup(outdir)


def setup_exit_handler() -> None:
    """
    Make sure that any managed subprocess gets shut down when the pipeline
    receives a SIGINT / SIGTERM.
    """

    def exit_handler(signum, __):
        signame = signal.Signals(signum).name
        log.warning(f"{signame} received, shutting down")
        # Kills all managed subprocesses
        # https://stackoverflow.com/q/67823770
        raise SystemExit(signum)

    signal.signal(signal.SIGTERM, exit_handler)
    signal.signal(signal.SIGINT, exit_handler)


def cleanup(directory: str) -> None:
    """
    Delete any temporary files created by a pipeline run in the given
    directory.
    """
    log.info(f"Running cleanup in directory: {directory!r}")


def run_command_line(cmd: CommandLine) -> None:
    """
    Run given command line via subprocess.check_call() and log its total run
    time.
    """
    program_name = cmd[0]
    cmd_str = " ".join(cmd)
    log.info(f"Running {program_name}")
    log.info(cmd_str)
    start_time = time.perf_counter()

    # NEXT: capture stderr / stdout
    # If we want to redirect to a logger, here's one possible solution:
    # https://stackoverflow.com/q/35488927
    subprocess.check_call(cmd)

    end_time = time.perf_counter()
    run_time_seconds = end_time - start_time
    log.info(f"{program_name} finished in {run_time_seconds:.2f} seconds")


def run_command_line_in_workdir(cmd: CommandLine, workdir: str) -> None:
    """
    Same as run_command_line() but do it with the working directory temporarily
    changed to `workdir`.
    """
    with ChangeDir(workdir):
        run_command_line(cmd)
