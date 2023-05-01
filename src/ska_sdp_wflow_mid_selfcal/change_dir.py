import os
from contextlib import contextmanager


@contextmanager
def change_dir(new_dir: str):
    """
    Context manager that changes the current working directory.

    Args:
        new_dir: string containing the path of the new working directory.

    Raises:
        FileNotFoundError: if the specified directory does not exist.

    Example::

        with change_dir('/path/to/new/directory'):
            # Code that runs in the new directory
            print(os.getcwd())

        # Code that runs in the original directory
        print(os.getcwd())
    """
    old_dir = os.getcwd()
    try:
        os.chdir(new_dir)
        yield
    finally:
        os.chdir(old_dir)
