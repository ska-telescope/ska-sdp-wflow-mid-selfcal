import datetime
from pathlib import Path


def create_pipeline_output_subdirectory(base_directory: Path) -> Path:
    """
    Creates a new subdirectory inside the given base directory for storing the
    output of a pipeline run. The name of the directory is based on the exact
    time at which this function was called.

    Args:
        base_directory: A string with the path to the base directory where the
            new subdirectory will be created.

    Returns:
        A string with the path to the newly created subdirectory.

    Raises:
        FileNotFoundError: If `base_directory` does not exist.

    Example:
        >>> create_pipeline_output_subdirectory("/home/user/results/")
        '/home/user/results/selfcal_20230405_091202_123456'
    """
    subdir_name = datetime.datetime.now().strftime("selfcal_%Y%m%d_%H%M%S_%f")
    subdir_path = base_directory.absolute() / subdir_name
    subdir_path.mkdir(parents=False, exist_ok=False)
    return subdir_path
