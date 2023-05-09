from ska_sdp_wflow_mid_selfcal.set_env import set_env
from ska_sdp_wflow_mid_selfcal.slurm_support import (
    get_slurm_allocated_resources,
)


def test_slurm_allocated_resources():
    """
    Self-explanatory.
    """
    cx_nodes = set_env("SLURM_JOB_NUM_NODES", 4)
    cx_cpus = set_env("SLURM_CPUS_ON_NODE", 38)
    cx_mem = set_env("SLURM_MEM_PER_NODE", 42000)
    with cx_nodes, cx_cpus, cx_mem:
        res = get_slurm_allocated_resources()
        assert res.nodes == 4
        assert res.cpus == 38
        assert res.mem_mb == 42000


def test_slurm_allocated_resources_num_nodes_only():
    """
    Self-explanatory.
    """
    with set_env("SLURM_JOB_NUM_NODES", 4):
        res = get_slurm_allocated_resources()
        assert res.nodes == 4
        assert res.cpus is None
        assert res.mem_mb is None
