import logging
import shlex
import signal
import time
from typing import Sequence

from ska_sdp_wflow_mid_selfcal.change_dir import ChangeDir
from ska_sdp_wflow_mid_selfcal.cleanup import cleanup
from ska_sdp_wflow_mid_selfcal.logging_setup import LOGGER, LOGGER_NAME
from ska_sdp_wflow_mid_selfcal.multi_node_support import (
    get_num_allocated_nodes,
    make_multi_node,
)
from ska_sdp_wflow_mid_selfcal.selfcal_logic import command_line_generator
from ska_sdp_wflow_mid_selfcal.singularify import CommandLine, singularify
from ska_sdp_wflow_mid_selfcal.stream_capture import (
    check_call_with_stream_capture,
)


def selfcal_pipeline(
    input_ms_list: list[str],
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
        input_ms_list: List of paths (strings) to the input Measurement Sets.
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
            input_ms_list,
            outdir=outdir,
            size=size,
            scale=scale,
            clean_iters=clean_iters,
            phase_only_cycles=phase_only_cycles,
        )
        num_nodes = get_num_allocated_nodes()
        LOGGER.info(f"Number of allocated nodes: {num_nodes}")

        for base_cmd in generator:
            cmd = singularify(base_cmd, singularity_image)
            cmd = make_multi_node(cmd)
            run_command_line_in_workdir(cmd, outdir)

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
    with ChangeDir(workdir):
        run_command_line(cmd)


def _get_program_name(cmd: CommandLine) -> str:
    if "wsclean" in cmd or "wsclean-mp" in cmd:
        return "wsclean"
    if "DP3" in cmd:
        return "DP3"
    return cmd[0]
