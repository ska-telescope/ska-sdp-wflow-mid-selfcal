import os
import shlex
from contextlib import contextmanager
from typing import Any

from ska_sdp_wflow_mid_selfcal.multi_node_support import make_multi_node


@contextmanager
def setenv(key: str, value: Any):
    """
    Context manager to temporarily set an environment variable. Attempts to
    convert `value` to `str` beforehand.
    """
    previous_value = os.environ.get(key, None)

    try:
        value = str(value)
        os.environ[key] = value
        yield
    finally:
        if previous_value is None and key in os.environ:
            del os.environ[key]
        else:
            os.environ[key] = previous_value


def test_setenv_on_existing_variable():
    """
    Self-explanatory.
    """
    key = "DEF_AN_EXISTING_ENV_VARIABLE"
    old_val = "old"
    os.environ[key] = old_val

    new_val = "new"
    try:
        with setenv(key, new_val):
            assert os.environ[key] == new_val
        assert os.environ[key] == old_val
    finally:
        del os.environ[key]


def test_setenv_on_non_existent_variable():
    """
    Self-explanatory.
    """
    key = "DEF_NOT_AN_ENV_VARIABLE"
    val = "Anything, really!"
    with setenv(key, val):
        assert os.environ[key] == val
    assert key not in os.environ


def test_make_multi_node_wsclean_command_one_node():
    """
    Check that a wsclean command is left unchanged when only 1 node is
    available.
    """
    cmd = shlex.split("wsclean -size 4096 4096 input.ms")
    # We can safely assume that in the pytest environment, the
    # SLURM_JOB_NUM_NODES env variable will be unset
    result = make_multi_node(cmd)
    assert result == cmd


def test_make_multi_node_wsclean_command_two_nodes():
    """
    Check that a wsclean command is transformed into a mpirun wsclean-mp
    command when 2+ nodes are available.
    """
    cmd = shlex.split("wsclean -size 4096 4096 input.ms")
    with setenv("SLURM_JOB_NUM_NODES", 2):
        result = make_multi_node(cmd)
    expected_result = shlex.split(
        "mpirun -np 2 -npernode 1 wsclean-mp -channels-out 2 "
        "-fit-spectral-pol 1 -deconvolution-channels 1 -join-channels "
        "-size 4096 4096 input.ms"
    )
    assert result == expected_result


def test_make_multi_node_dp3_command_two_nodes():
    """
    Check that a DP3 command is left unchanged even with multiple
    nodes available.
    """
    cmd = shlex.split(
        "DP3 msin=/input/data.ms msout=/input/data.ms "
        "msout.datacolumn=CORRECTED_DATA steps=[gaincal] "
        "gaincal.caltype=diagonal gaincal.maxiter=50 "
        "gaincal.usemodelcolumn=true gaincal.applysolution=true"
    )
    with setenv("SLURM_JOB_NUM_NODES", 2):
        result = make_multi_node(cmd)
    assert result == cmd
