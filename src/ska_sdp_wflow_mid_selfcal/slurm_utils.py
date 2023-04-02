import os
from typing import Sequence

import jinja2


def generate_slurm_script(
    sys_argv: Sequence[str],
    *,
    cpus_per_task: int,
    ram_gb: float,
    partition: str
) -> str:
    """
    Generate a slurm script wrapping the command line with which this app was
    called, minus the options related to SLURM.

    Args:
        sys_argv (Sequence[str]): The list of command line arguments collected
            by the pipeline app via sys.argv.
        outdir (str): Output directory where the pipeline shall write its data
            products.

    Returns:
        script (str): The contents of the generated SLURM script.
    """
    # NOTE: Useful post on SLURM terminology and how to configure nodes,
    # tasks-per-nodes, cpus-per-task, etc.
    # https://stackoverflow.com/q/51139711
    template_path = os.path.join(
        os.path.dirname(__file__), "..", "templates", "slurm_script.jinja2"
    )
    with open(template_path, "r", encoding="utf-8") as fobj:
        template = jinja2.Template(
            fobj.read(), undefined=jinja2.StrictUndefined
        )

    return template.render(
        pipeline_command=trimmed_pipeline_command(sys_argv),
        cpus_per_task=cpus_per_task,
        ram_gb=ram_gb,
        partition=partition
    )


def trimmed_pipeline_command(sys_argv: Sequence[str]) -> str:
    """
    Returns the command line with which the pipeline app was called, minus the
    options related to SLURM.
    """
    trimmed_argv = filter(lambda s: "slurm" not in s, sys_argv)
    return " ".join(trimmed_argv)
