import os
from typing import Sequence, Any

import jinja2


def generate_slurm_script(
    pipeline_args: dict[str, Any],
    *,
    cpus_per_task: int,
    ram_gb: float,
    partition: str
) -> str:
    """
    Generate a slurm script containing the appropriate command-line to call the
    pipeline.
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
        pipeline_command=generate_pipeline_command(pipeline_args),
        cpus_per_task=cpus_per_task,
        ram_gb=ram_gb,
        partition=partition
    )


def generate_pipeline_command(pipeline_cmdline_args: dict[str, Any]) -> str:
    """
    Returns the command line with which the pipeline app was called, minus the
    options related to SLURM.
    """
    arguments = ["mid-selfcal-pipeline"]
    for key, value in pipeline_cmdline_args.items():
        key = key.replace("_", "-")
        arguments.append(f"--{key}")
        arguments.append(str(value))
    return " ".join(arguments)
