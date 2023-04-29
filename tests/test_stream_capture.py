import subprocess

import pytest

from ska_sdp_wflow_mid_selfcal.stream_capture import (
    check_call_with_stream_capture,
)


def test_check_call_with_stream_capture():
    """
    Tests the check_call_with_stream_capture function by running a simple
    Python script that prints some output to stdout and stderr.
    """
    code_lines = [
        "import sys",
        "for i in range(3):",
        "    print('Running', flush=True)",
        "    print('Test', flush=True)",
        "    print('Output', flush=True)",
        "    print('Is it?', flush=True,file=sys.stderr)",
    ]

    cmdline = ["python", "-c", "\n".join(code_lines)]

    captured_stdout = []
    captured_stderr = []

    def stdout_consumer(line: str):
        captured_stdout.append(line)

    def stderr_consumer(line: str):
        captured_stderr.append(line)

    check_call_with_stream_capture(cmdline, stdout_consumer, stderr_consumer)

    assert captured_stdout == 3 * ["Running", "Test", "Output"]
    assert captured_stderr == 3 * ["Is it?"]


def test_check_call_with_stream_capture_raises_on_nonzero_exit_code():
    """
    Check that CalledProcessError is raised if command exits with non-zero
    code.
    """
    cmdline = ["ls", "/definitely/non/existent/path/"]

    def null_consumer(__: str):
        pass

    with pytest.raises(subprocess.CalledProcessError):
        check_call_with_stream_capture(cmdline, null_consumer, null_consumer)
