from pathlib import Path
from typing import Iterable, Iterator, Optional

CommandLine = list[str]


def _extract_abspath(arg: str) -> Optional[Path]:
    """
    Find an absolute path in a string that represents a command-line argument.
    Note that DP3 arguments containing an absolute path may look
    like `msin=/data/input.ms`. Returns None if `arg` does not contain an
    absolute path.
    """
    if arg.startswith("/"):
        return Path(arg)
    if "=/" in arg:
        __, path_without_lead_slash = arg.split("=/")
        return Path("/" + path_without_lead_slash)
    return None


def _iter_unique(iterable: Iterable) -> Iterator:
    """
    Iterate over unique values in iterable. This function serves the purpose of
    an ordered set.
    """
    seen = set()
    for val in iterable:
        if val not in seen:
            seen.add(val)
            yield val


def singularify(
    command_line: CommandLine, singularity_image: str
) -> CommandLine:
    """
    Transform a command line so that it can be run within a Singularity
    container. NOTE: Any argument that contains a path in `command_line` must
    be absolute, i.e. have a leading slash. See Notes below.

    This function takes a command line represented as a list of strings, and a
    path to a Singularity image. It replaces any absolute path found on the
    command line with a path that is relative to a mount point within the
    container. It then prefixes the resulting command line with `singularity
    exec`, appends the path to the Singularity image and any necessary
    bind-mount arguments.

    Args:
        command_line: The original command line as a list of strings.
        singularity_image: The path to the Singularity image to use.

    Returns:
        A new command line that can be used to run the specified command line
        within a Singularity container.

    Notes:
        There are two rules to detect path-containing arguments: either they
        start with a forward slash, or they contain the sequence "=/" in order
        for the function to work with DP3, example: `msin=/data/input.ms`.

    Example:
        >>> command = ["python", "/path/to/script.py", "--data", "/path/to/file.txt"]
        >>> singularity_image = "/other/path/image.sif"
        >>> new_command = singularify(command, singularity_image)
        >>> print(new_command)
        ['singularity', 'exec', '--bind', '/path/to:/mnt/path/to', '/other/path/image.sif', 'python', '/mnt/path/to/script.py', '--data', '/mnt/path/to/file.txt']
    """  # noqa: E501, pylint: disable=line-too-long

    # NOTE: we need to make sure the generated command line runs from any
    # working directory, hence making paths absolute
    singularity_image = str(Path(singularity_image).absolute())

    # Dictionary {argument_string: (source_abspath, target_abspath)}
    # This is used to replace source paths (as seen from the host)
    # by target paths (as seen from the singularity container) when generating
    # the output command line.
    arg_properties_dict: dict[str, tuple[Path, Path]] = {}

    # List of tuples (source_dir_path, target_dir_path)
    # This is used to generate the "--bind {SOURCE}:{TARGET}" statements
    bind_mount_pairs: list[tuple[Path, Path]] = []

    for arg in command_line:
        source_path = _extract_abspath(arg)
        if not source_path:
            continue

        target_path = Path(f"/mnt{source_path}")
        bind_mount_pairs.append((source_path.parent, target_path.parent))
        arg_properties_dict[arg] = (source_path, target_path)

    new_command_line = ["singularity", "exec"]

    for source_dir, target_dir in _iter_unique(bind_mount_pairs):
        new_command_line.append("--bind")
        new_command_line.append(f"{source_dir}:{target_dir}")

    new_command_line.append(singularity_image)

    def amend_argument(arg: str) -> str:
        if arg not in arg_properties_dict:
            return arg
        source, target = arg_properties_dict[arg]
        return arg.replace(str(source), str(target))

    new_command_line.extend([amend_argument(arg) for arg in command_line])
    return new_command_line
