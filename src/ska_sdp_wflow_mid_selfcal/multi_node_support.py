import os
from typing import Sequence


def make_multi_node(command: Sequence[str]) -> list[str]:
    """
    If given a wsclean command and multiple nodes are available, return a
    transformed, wsclean-mp command that can be run on multiple nodes
    via mpirun. Otherwise, just return `command`.
    """
    num_nodes = get_num_allocated_nodes()
    if "wsclean" not in command or not num_nodes > 1:
        return command
    return _make_mpirun_wsclean_mp_command(command, num_nodes)


def get_num_allocated_nodes() -> int:
    """
    If in a SLURM environment, return the number of allocated nodes.
    Return 1 otherwise.
    """
    try:
        return int(os.environ["SLURM_JOB_NUM_NODES"])
    except KeyError:
        return 1


def _make_mpirun_wsclean_mp_command(
    wsclean_regular_command: Sequence[str], num_nodes: int
):
    """
    Given a regular, single-node wsclean command, create a wsclean-mp command
    that can be executed with mpirun.
    """
    wsclean_mp_command = _make_wsclean_mp_command(
        wsclean_regular_command, num_nodes
    )
    prefix = ["mpirun", "-np", str(num_nodes), "-npernode", "1"]
    return prefix + wsclean_mp_command


def _make_wsclean_mp_command(
    wsclean_regular_command: Sequence[str], num_nodes: int
) -> list[str]:
    new_command = list(wsclean_regular_command).copy()
    index = new_command.index("wsclean")
    new_command[index] = "wsclean-mp"

    additional_wsclean_args = [
        "-channels-out",
        str(num_nodes),
        "-fit-spectral-pol",
        str(1),
        "-deconvolution-channels",
        str(1),
        "-join-channels",
    ]

    return (
        new_command[: index + 1]
        + additional_wsclean_args
        + new_command[index + 1 :]
    )
