import os


class ChangeDir:
    """
    Context manager that temporarily changes the current working directory.
    """

    def __init__(self, new_dir: str) -> None:
        """
        Temporarily change the current working directory.

        Args:
            new_dir: string containing the path of the new working directory.

        Usage:
            with ChangeDir('/path/to/new/directory'):
                # Code that runs in the new directory
                print(os.getcwd())

            # Code that runs in the original directory
            print(os.getcwd())
        """
        self._new_dir = new_dir
        self._old_dir = None

    def __enter__(self) -> None:
        self._old_dir = os.getcwd()
        os.chdir(self._new_dir)

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        os.chdir(self._old_dir)
