import logging
import sys

from .pipeline_app import base_parser
from ska_sdp_wflow_mid_selfcal.slurm_utils import generate_slurm_script


log = logging.getLogger("mid-selfcal")


SLURM_PARSER_ARGS = {
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


def extended_parser():
    parser = base_parser()
    group = parser.add_argument_group("SLURM options")
    for param_name, param_kwargs in SLURM_PARSER_ARGS.items():
        group.add_argument(f"--{param_name}", **param_kwargs)
    return parser


def main():
    """
    Entry point for the SLURM selfcal pipeline app.
    """
    args = extended_parser().parse_args()

    kwargs = {}
    for key in SLURM_PARSER_ARGS.keys():
        attr_name = key.replace("-", "_")
        attr_value = getattr(args, attr_name)
        kwargs[attr_name] = attr_value

    script = generate_slurm_script(sys.argv, **kwargs)
    print(script)


if __name__ == "__main__":
    main()
