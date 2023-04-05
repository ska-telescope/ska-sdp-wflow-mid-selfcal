import pytest

from ska_sdp_wflow_mid_selfcal.pipeline import command_line_generator


def test_command_line_generator():
    """
    Tests whether command_line_generator() returns the expected command line
    format when optional WSClean parameters are or are NOT provided.

    Note: this does NOT test for whether WSClean options are flagged with
          the right syntax, order, or values.
    """

    input_ms = "input.ms"
    outdir = "/data"

    wsclean_opts = ["-size", "1000", "1000", "-niter", "10000"]
    gen = command_line_generator(
        input_ms, outdir=outdir, wsclean_opts=wsclean_opts
    )
    expected_output = (
        ["wsclean"] + wsclean_opts + ["-name", f"{outdir}/wsclean", input_ms]
    )
    assert expected_output == list(gen)[0]

    gen = command_line_generator(input_ms, outdir=outdir)
    expected_output = ["wsclean", "-name", f"{outdir}/wsclean", "input.ms"]
    assert expected_output == list(gen)[0]


def test_command_line_generator_raises_if_wsclean_opts_contains_name():
    """
    Test we get a ValueError if '-name' is specified as part of wsclean_opts
    """
    gen = command_line_generator(
        "input.ms", outdir="/data", wsclean_opts=["-name", "custom_name"]
    )
    with pytest.raises(ValueError):
        list(gen)
