import os
from dataclasses import dataclass
from typing import Optional

from .logging_setup import LOGGER


@dataclass(frozen=True)
class SlurmResources:
    """
    Simple dataclass describing the compute resources allocated by SLURM, as
    read from the SLURM_* environment variables.
    """

    nodes: Optional[int]
    """ Number of allocated nodes """

    cpus: Optional[int]
    """ Number of CPUs allocated on every node """

    mem_mb: Optional[int]
    """ Memory allocated on every node in MB """


def get_slurm_allocated_resources() -> SlurmResources:
    """
    Returns a `SlurmResources` object describing the compute resources
    allocated by SLURM.
    """

    def getenv(key: str, vtype: type):
        strval = os.environ.get(key, None)
        return vtype(strval) if strval is not None else None

    return SlurmResources(
        nodes=getenv("SLURM_JOB_NUM_NODES", int),
        cpus=getenv("SLURM_CPUS_ON_NODE", int),
        mem_mb=getenv("SLURM_MEM_PER_NODE", int),
    )


def log_slurm_allocated_resources() -> None:
    """
    If running in a SLURM environment, log the resources allocated by the
    SLURM scheduler.
    """
    res = get_slurm_allocated_resources()

    if res.nodes:
        LOGGER.info(f"SLURM allocated nodes: {res.nodes}")

    if res.cpus:
        LOGGER.info(f"SLURM allocated CPUs/node: {res.cpus}")

    # NOTE: On CSD3, the SLURM scheduler does not set $SLURM_MEM_PER_NODE
    # unless the user has requested a specific amount of memory via e.g. --mem
    if res.mem_mb:
        LOGGER.info(f"SLURM allocated RAM: {res.mem_mb} MB")
