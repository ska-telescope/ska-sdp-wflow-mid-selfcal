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
