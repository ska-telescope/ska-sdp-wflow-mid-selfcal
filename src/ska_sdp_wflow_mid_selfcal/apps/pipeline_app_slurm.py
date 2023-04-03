import argparse
import logging

from .pipeline_app import base_parser
from ska_sdp_wflow_mid_selfcal.slurm_utils import generate_slurm_script


log = logging.getLogger("mid-selfcal")


SLURM_ARGS_DEFINITION = {
    "cpus-per-task": {
        "type": int,
        "default": 1,
        "help": "Number of CPUs to request.",
    },
    "ram-gb": {
        "type": float,
        "default": 32.0,
        "help": "Total RAM to request, in gigabytes.",
    },
    "partition": {
        "type": str,
        "default": "skylake",
        "help": "SLURM partition on which to run the job.",
    },
}

SLURM_ARGNAMES = list(SLURM_ARGS_DEFINITION.keys())

SLURM_ARGNAMES_WITH_UNDERSCORES = list(
    map(lambda k: k.replace("-", "_"), SLURM_ARGNAMES)
)


def extended_parser() -> argparse.ArgumentParser:
    """
    Returns a parser with both the pipeline app options *and* the SLURM options
    added.
    """
    parser = base_parser()
    group = parser.add_argument_group("SLURM options")
    for name, kwargs in SLURM_ARGS_DEFINITION.items():
        group.add_argument(f"--{name}", **kwargs)
    return parser


def main():
    """
    Entry point for the SLURM selfcal pipeline app.
    """
    args = extended_parser().parse_args()

    args_dict = vars(args)
    args_keys = set(args_dict.keys())
    slurm_args_keys = set(
        key.replace("-", "_") for key in SLURM_ARGS_DEFINITION
    )
    base_args_keys = args_keys.difference(slurm_args_keys)

    slurm_args_dict = {key: args_dict[key] for key in slurm_args_keys}
    base_args_dict = {key: args_dict[key] for key in base_args_keys}

    script = generate_slurm_script(base_args_dict, **slurm_args_dict)
    print(script)


if __name__ == "__main__":
    main()
