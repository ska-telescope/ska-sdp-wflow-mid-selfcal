import argparse
import logging
import os
import sys

from ska_sdp_wflow_mid_selfcal import selfcal_pipeline

log = logging.getLogger("mid-selfcal")


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments into a convenient object.
    """
    parser = argparse.ArgumentParser(
        description="Launch the SKA Mid self-calibration pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--slurm",
        action="store_true",
        help=(
            "Generate a slurm script out of the given command line and "
            "submit it to the queue."
        ),
    )
    parser.add_argument(
        "--base-outdir",
        type=str,
        default=os.getcwd(),
        help=(
            "Base output directory; a uniquely named sub-directory will be "
            "created, in which all products will be written."
        ),
    )
    return parser.parse_args()


def setup_logging() -> None:
    """
    Configure the logger(s) used by the pipeline.
    """
    logging.basicConfig(
        level="DEBUG",
        format="[%(levelname)s - %(asctime)s - %(name)s] %(message)s",
    )


def create_unique_output_directory(base_outdir: str) -> str:
    """
    Create a sub-directory of `base_outdir` in which the pipeline outputs
    will be written.
    """
    outdir = base_outdir
    log.info(f"Created output directory: {outdir}")
    return outdir


def generate_slurm_script(argv: list[str]) -> str:
    """
    Generate a slurm script wrapping the command line with which this app was
    called, minus the options related to SLURM.
    `argv` is the list of command-line arguments as returned by `sys.argv`.
    """
    command_line = " ".join(argv).replace("--slurm", "")
    script_lines = [
        "#SLURM Header",
        "module load whatever",
        "conda activate some_env",
        command_line,
    ]
    script = "\n".join(script_lines)
    return script


def run_slurm_mode(argv: list[str]) -> None:
    """
    Run the program in SLURM mode. That is, generate a slurm script wrapping
    the command line with which this app was called, minus the options related
    to SLURM, and print script to stdout.
    `argv` is the list of command-line arguments as returned by `sys.argv`.
    """
    log.info("Running in SLURM mode")
    script = generate_slurm_script(argv)
    print(script)


def main():
    """
    Entry point for the selfcal pipeline app.
    """
    args = parse_args()
    setup_logging()
    outdir = create_unique_output_directory(args.base_outdir)

    if args.slurm:
        run_slurm_mode(sys.argv)
        return

    selfcal_pipeline(outdir=outdir)


if __name__ == "__main__":
    main()
