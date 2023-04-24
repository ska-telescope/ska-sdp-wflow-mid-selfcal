import argparse
import logging
import os

from ska_sdp_wflow_mid_selfcal import selfcal_pipeline
from ska_sdp_wflow_mid_selfcal.directory_creation import (
    create_pipeline_output_subdirectory,
)
from ska_sdp_wflow_mid_selfcal.logging_setup import setup_logging

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
        "--singularity-image",
        type=os.path.realpath,
        required=True,
        help=(
            "Path to the singularity image file with both wsclean "
            "and DP3 installed."
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
    parser.add_argument(
        "input_ms",
        type=os.path.realpath,
        help="Input measurement set.",
    )
    return parser.parse_args()


def main():
    """
    Entry point for the selfcal pipeline app.
    """
    args = parse_args()
    outdir = create_pipeline_output_subdirectory(args.base_outdir)
    logfile_path = os.path.join(outdir, "logfile.txt")
    setup_logging(logfile_path)

    log.info(f"Created output directory: {outdir!r}")
    selfcal_pipeline(
        args.input_ms,
        outdir=outdir,
        singularity_image=args.singularity_image
    )


if __name__ == "__main__":
    main()
