import os
from contextlib import contextmanager
from typing import Any


@contextmanager
def set_env(key: str, value: Any):
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
