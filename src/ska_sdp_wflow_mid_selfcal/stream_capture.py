import subprocess
from threading import Thread
from typing import Any, Callable


def stream_capture(
    cmd: list[str],
    stdout_consumer: Callable[[str], Any],
    stderr_consumer: Callable[[str], Any],
):
    """
    Launches a subprocess and captures its standard output and error
    streams in separate threads, calling the specified
    consumers for each line of output.

    Args:
        cmd: The commandline to execute in a subprocess, as a list of strings.
        stdout_consumer: A callable function that accepts a string argument
            representing a line of standard output from the subprocess.
        stderr_consumer: A callable function that accepts a string argument
            representing a line of standard error from the subprocess.
    Raises:
        subprocess.CalledProcessError: if the subprocess exited
            with a non-zero code.
    """
    with subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    ) as process:

        def process_stdout():
            for line in process.stdout:
                stdout_consumer(line.rstrip())

        def process_stderr():
            for line in process.stderr:
                stderr_consumer(line.rstrip())

        errthread = Thread(target=process_stderr)
        outthread = Thread(target=process_stdout)
        errthread.start()
        outthread.start()
        outthread.join()
        errthread.join()

    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, cmd)
