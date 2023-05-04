from collections import defaultdict
from pathlib import Path
from typing import Iterable, Iterator

CommandLine = list[str]


def _extract_abspaths(arg: str) -> list[Path]:
    """
    Find all absolute paths in a string that represents a command-line
    argument for DP3 or wsclean.
    Note that DP3 arguments containing an absolute path may look like:
        - `msin=/data/input.ms`
        - `msin=[/data/band1.ms,/data/band2.ms]`
    """
    if arg.startswith("/"):
        return [Path(arg)]

    if "=" in arg:
        __, tail = arg.split("=")
        path_strings = tail.strip("[]").split(",")
        return [Path(s) for s in path_strings if s.startswith("/")]

    return []


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
        start with a forward slash, or they look like
        `msin=[/path/1.ms,/path/2.ms]` in order for the function to work with
        DP3.

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

    # Dictionary
    # {
    #     argument_string: [
    #         (source_abspath1, target_abspath1),
    #         (source_abspath2, target_abspath2),
    #         ...
    #         ]
    # }
    # Each argument contains one or more (in the case of DP3) host absolute
    # paths to be substituted by target absolute paths (as seen from inside
    # the container).
    arg_properties_dict: dict[str, list[tuple[Path, Path]]] = defaultdict(list)

    # List of tuples (source_dir_path, target_dir_path)
    # This is used to generate the "--bind {SOURCE}:{TARGET}" statements
    bind_mount_pairs: list[tuple[Path, Path]] = []

    for arg in command_line:
        source_paths = _extract_abspaths(arg)
        for source_path in source_paths:
            target_path = Path(f"/mnt{source_path}")
            bind_mount_pairs.append((source_path.parent, target_path.parent))
            arg_properties_dict[arg].append((source_path, target_path))

    new_command_line = ["singularity", "exec"]

    for source_dir, target_dir in _iter_unique(bind_mount_pairs):
        new_command_line.append("--bind")
        new_command_line.append(f"{source_dir}:{target_dir}")

    new_command_line.append(singularity_image)

    def amend_argument(arg: str) -> str:
        replacement_pairs = arg_properties_dict[arg]
        for source, target in replacement_pairs:
            arg = arg.replace(str(source), str(target))
        return arg

    new_command_line.extend([amend_argument(arg) for arg in command_line])
    return new_command_line
