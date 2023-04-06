import logging
import os
import signal
import subprocess
import time
from typing import Iterator, Optional

from ska_sdp_wflow_mid_selfcal.change_dir import ChangeDir

CommandLine = list[str]


log = logging.getLogger("mid-selfcal")


def selfcal_pipeline(
    input_ms: str, *, outdir: str, wsclean_opts: Optional[list[str]] = None
) -> None:
    """
    Run the direction-independent self-calibration pipeline.

    Args:
        input_ms: path to the input Measurement Set as a string
        outdir: path to the directory where all output files will be written
        wsclean_opts: list of strings with additional user-defined options to
            forward to WSCLEAN. "-name" is NOT allowed, as this option
            is managed by the pipeline itself.
    """
    setup_exit_handler()
    try:
        generator = command_line_generator(
            input_ms, outdir=outdir, wsclean_opts=wsclean_opts
        )
        for cmd in generator:
            run_command_line_in_workdir(cmd, outdir)
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


def command_line_generator(
    input_ms: str, *, outdir: str, wsclean_opts: Optional[list[str]] = None
) -> Iterator[CommandLine]:
    """
    Iterator that generates the correct command lines to execute to perform
    the self-calibration loop.
    """
    if wsclean_opts is None:
        wsclean_opts = []

    if "-name" in wsclean_opts:
        raise ValueError("-name must not be specified in wsclean_opts")

    # Instruct wsclean to save the output files in `outdir`, with the default
    # base file name "wsclean"
    image_prefix = os.path.join(outdir, "wsclean")
    yield ["wsclean"] + wsclean_opts + ["-name", image_prefix] + [input_ms]


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
