import os

from ska_sdp_wflow_mid_selfcal.set_env import set_env


def test_set_env_on_existing_variable():
    """
    Self-explanatory.
    """
    key = "DEF_AN_EXISTING_ENV_VARIABLE"
    old_val = "old"
    os.environ[key] = old_val

    new_val = "new"
    try:
        with set_env(key, new_val):
            assert os.environ[key] == new_val
        assert os.environ[key] == old_val
    finally:
        del os.environ[key]


def test_set_env_on_non_existent_variable():
    """
    Self-explanatory.
    """
    key = "DEF_NOT_AN_ENV_VARIABLE"
    val = "Anything, really!"
    with set_env(key, val):
        assert os.environ[key] == val
    assert key not in os.environ
