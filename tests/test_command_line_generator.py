from ska_sdp_wflow_mid_selfcal.pipeline import command_line_generator


def test_command_line_generator():
    """
    Tests whether command_line_generator() returns the expected command line
    format when optional WSClean parameters are or are NOT provided.

    Note: this does NOT test for whether WSClean options are flagged with
          the right syntax, order, or values.
    """

    input_ms = "input.ms"
    wsclean_opts = "-size 1000 1000 -niter 10000"
    expected_output = [
        "wsclean",
        "-size",
        "1000",
        "1000",
        "-niter",
        "10000",
        "input.ms",
    ]
    gen = command_line_generator(input_ms, wsclean_opts=wsclean_opts)
    assert expected_output == list(gen)[0]

    wsclean_opts = None
    expected_output = ["wsclean", "input.ms"]
    gen = command_line_generator(input_ms, wsclean_opts=wsclean_opts)
    assert expected_output == list(gen)[0]
