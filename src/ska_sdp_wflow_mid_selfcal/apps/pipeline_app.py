import argparse
import logging
import os

from ska_sdp_wflow_mid_selfcal import selfcal_pipeline

log = logging.getLogger("mid-selfcal")


def base_parser() -> argparse.ArgumentParser:
    """
    Returns a parser with all the common options between the pipeline app
    and its SLURM counterpart.
    """
    parser = argparse.ArgumentParser(
        description="Launch the SKA Mid self-calibration pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
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
    return parser


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


def main():
    """
    Entry point for the selfcal pipeline app.
    """
    args = base_parser().parse_args()
    setup_logging()
    outdir = create_unique_output_directory(args.base_outdir)
    selfcal_pipeline(outdir=outdir)


if __name__ == "__main__":
    main()
