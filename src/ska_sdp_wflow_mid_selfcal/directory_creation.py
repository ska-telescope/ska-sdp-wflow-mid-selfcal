import datetime
from pathlib import Path


def create_pipeline_output_subdirectory(base_directory: Path) -> Path:
    """
    Creates a new subdirectory inside the given base directory for storing the
    output of a pipeline run. The name of the directory is based on the exact
    time at which this function was called.

    Args:
        base_directory (Path): The base directory where the subdirectory will
        be created.

    Returns:
        Path: The path of the created subdirectory.

    Raises:
        FileExistsError: If the subdirectory already exists.

    Example:
        >>> base_dir = Path('/path/to/base_directory')
        >>> sub_dir = create_pipeline_output_subdirectory(base_dir)
        >>> print(sub_dir)
        /path/to/base_directory/selfcal_20230702_145127_123456
    """
    subdir_name = datetime.datetime.now().strftime("selfcal_%Y%m%d_%H%M%S_%f")
    subdir_path = base_directory.absolute() / subdir_name
    subdir_path.mkdir(parents=False, exist_ok=False)
    return subdir_path
