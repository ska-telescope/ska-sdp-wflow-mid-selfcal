import logging
import os
import signal
import subprocess
import time
from typing import Iterator, Optional

CommandLine = list[str]


log = logging.getLogger("mid-selfcal")


def selfcal_pipeline(
    input_ms: str, *, outdir: str, wsclean_opts: Optional[str] = None
) -> None:
    """
    Run the direction-independent self-calibration pipeline, writing any file
    output in directory "outdir".
    """
    setup_exit_handler()
    try:
        generator = command_line_generator(
            input_ms, outdir=outdir, wsclean_opts=wsclean_opts
        )
        for cmd in generator:
            run_program(cmd)
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
    input_ms: str, *, outdir: str, wsclean_opts: Optional[str] = None
) -> Iterator[CommandLine]:
    """
    Iterator that generates the correct command lines to execute to perform
    the self-calibration loop.
    """
    wsclean_opts_list = wsclean_opts.split() if wsclean_opts else []

    # Instruct wsclean to save the output files in `outdir`
    image_prefix = os.path.join(outdir, "wsclean")
    wsclean_opts_list.extend(["-name", image_prefix])

    yield ["wsclean"] + wsclean_opts_list + [input_ms]


def run_program(cmd: CommandLine) -> None:
    """
    Run given command line via subprocess.check_call() and logs its total run
    time.
    """
    program_name = cmd[0]
    log.info(f"Starting {program_name}")
    log.info(f"Running command line: {cmd}")
    start_time = time.perf_counter()

    # NEXT: capture stderr / stdout
    # If we want to redirect to a logger, here's one possible solution:
    # https://stackoverflow.com/q/35488927
    subprocess.check_call(cmd)

    end_time = time.perf_counter()
    run_time_seconds = end_time - start_time
    log.info(f"{program_name} finished in {run_time_seconds:.2f} seconds")
