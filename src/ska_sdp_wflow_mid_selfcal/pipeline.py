import logging
import os
import shlex
import signal
import subprocess
import time
from typing import Optional, Sequence

from ._version import __version__
from .change_dir import change_dir
from .cleanup import cleanup, remove_unnecessary_fits_files
from .logging_setup import LOGGER, LOGGER_NAME
from .multi_node_support import make_multi_node
from .selfcal_logic import (
    TEMPORARY_MS,
    command_line_generator,
    dp3_merge_command,
)
from .singularify import CommandLine, singularify
from .slurm_support import log_slurm_allocated_resources
from .stream_capture import check_call_with_stream_capture


# pylint: disable=too-many-locals
def selfcal_pipeline(
    input_ms_list: list[str],
    *,
    outdir: str,
    singularity_image: str,
    size: tuple[int, int],
    scale: str,
    initial_sky_model: Optional[str] = None,
    gaincal_solint: int = 1,
    gaincal_nchan: int = 0,
    clean_iters: Sequence[int] = (20, 100, 500),
    phase_only_cycles: Sequence[int] = (0,),
) -> None:
    """
    Run the direction-independent self-calibration pipeline.

    Args:
        input_ms_list: List of paths (strings) to the input Measurement Sets.
        outdir: path to the directory where all output files will be written
        singularity_image: path to the singularity image file with both wsclean
            and DP3 installed.
        size: size of the output image in pixels as an int tuple
            (width, height).
        scale: scale of a pixel, as a string such as "20asec" or "0.01deg".
        initial_sky_model: Optional path to a DP3 sky model file to use for an
            initial calibration, before the self-cal starts.
        gaincal_solint: number of time slots over which a gain solution is
            assumed to be constant. 0 means all time slots.
        gaincal_nchan: number of channels over which a gain solution is
            assumed to be constant. 0 means all channels.
        clean_iters: Maximum Clean iterations per self-cal cycle, as a list of
            integers. This does not include the final imaging stage where the
            image is deconvolved down to the noise floor. To run only the final
            imaging stage without selfcal, specify this argument without a
            value.
        phase_only_cycles: sequence of self-cal cycle indices (zero-based) in
            which to perform phase-only calibration. To avoid doing any
            phase-only cal cycles, specify this argument without a value.
    """
    setup_exit_handler()
    try:
        LOGGER.info(f"Running version: {__version__}")
        log_slurm_allocated_resources()

        # Merge all input MSes into one, because DP3's gaincal can only operate
        # on a single input MS. We do this even if there's only one input MS,
        # to guarantee we get a fresh new MS without pre-existing MODEL_DATA.
        # That will give run times more representative of a production system.
        LOGGER.info("Merging input measurement sets into one")
        temporary_ms = os.path.join(outdir, TEMPORARY_MS)
        merge_cmd = dp3_merge_command(input_ms_list, temporary_ms)
        run_command_line_in_workdir(
            singularify(merge_cmd, singularity_image), outdir
        )

        LOGGER.info(f"Input size in bytes: {get_bytesize(temporary_ms)}")

        # From there, perform self-cal in place on the merged MS
        generator = command_line_generator(
            temporary_ms,
            outdir=outdir,
            size=size,
            scale=scale,
            initial_sky_model=initial_sky_model,
            gaincal_solint=gaincal_solint,
            gaincal_nchan=gaincal_nchan,
            clean_iters=clean_iters,
            phase_only_cycles=phase_only_cycles,
        )
        for base_cmd in generator:
            cmd = singularify(base_cmd, singularity_image)
            cmd = make_multi_node(cmd)
            run_command_line_in_workdir(cmd, outdir)
            remove_unnecessary_fits_files(outdir)

        LOGGER.info("Pipeline run: SUCCESS")

    # pylint: disable=broad-exception-caught
    except (Exception, SystemExit) as err:
        LOGGER.exception(f"Error: {err!r}")
        LOGGER.error("Pipeline run: FAIL")

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
        LOGGER.warning(f"{signame} received, shutting down")
        # Kills all managed subprocesses
        # https://stackoverflow.com/q/67823770
        raise SystemExit(signum)

    signal.signal(signal.SIGTERM, exit_handler)
    signal.signal(signal.SIGINT, exit_handler)


def run_command_line(cmd: CommandLine) -> None:
    """
    Run given command line, and live-capture its standard output and error
    streams to Python loggers. Also log the total run time of the command
    at the end.
    """
    program_name = _get_program_name(cmd)
    LOGGER.info(f"Running {program_name}")
    cmd_str = shlex.join(cmd)
    LOGGER.info(cmd_str)

    subprocess_logger = logging.getLogger(f"{LOGGER_NAME}.{program_name}")

    start_time = time.perf_counter()
    check_call_with_stream_capture(
        cmd, subprocess_logger.debug, subprocess_logger.debug
    )
    end_time = time.perf_counter()
    run_time_seconds = end_time - start_time
    LOGGER.info(f"{program_name} finished in {run_time_seconds:.2f} seconds")


def run_command_line_in_workdir(cmd: CommandLine, workdir: str) -> None:
    """
    Same as run_command_line() but do it with the working directory temporarily
    changed to `workdir`.
    """
    with change_dir(workdir):
        run_command_line(cmd)


def get_bytesize(path: str) -> int:
    """
    Get the total size that a file or directory occupies on disk,
    as reported by `du`.
    """
    output = subprocess.check_output(["du", "-bs", path])
    bytesize_str, __ = output.split()
    return int(bytesize_str)


def _get_program_name(cmd: CommandLine) -> str:
    if "wsclean" in cmd or "wsclean-mp" in cmd:
        return "wsclean"
    if "DP3" in cmd:
        return "DP3"
    return cmd[0]
