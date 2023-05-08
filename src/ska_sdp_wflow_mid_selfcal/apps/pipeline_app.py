import argparse
import os

from .. import __version__, selfcal_pipeline
from ..directory_creation import create_pipeline_output_subdirectory
from ..logging_setup import LOGGER, setup_logging


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments into a convenient object.
    """
    parser = argparse.ArgumentParser(
        description="Launch the SKA Mid self-calibration pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=__version__)
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
        "--size",
        nargs=2,
        type=int,
        required=True,
        help="Output image size as two integers <width> <height>",
    )
    parser.add_argument(
        "--scale",
        type=str,
        required=True,
        help=('Scale of a pixel, as a string such as "20asec" or "0.01deg".'),
    )
    parser.add_argument(
        "--clean-iters",
        nargs="+",
        type=int,
        default=[20, 100, 500, 500_000],
        help=(
            "Maximum Clean iterations per self-cal cycle, as a list of "
            "integers. The number of calibration cycles is one less than the "
            "length of the list, as the final value is used to make the image "
            "after the last calibration."
        ),
    )
    parser.add_argument(
        "--phase-only-cycles",
        nargs="+",
        type=int,
        default=[0],
        help=(
            "List of self-cal cycle indices (zero-based) in which to perform "
            "phase-only calibration. A reasonable default is to run a "
            "phase-only calibration for the first cycle."
        ),
    )
    parser.add_argument(
        "--input-ms",
        nargs="+",
        required=True,
        type=os.path.realpath,
        help="Input measurement set(s).",
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

    LOGGER.info(f"Created output directory: {outdir!r}")
    selfcal_pipeline(
        args.input_ms,
        outdir=outdir,
        singularity_image=args.singularity_image,
        size=args.size,
        scale=args.scale,
        clean_iters=args.clean_iters,
        phase_only_cycles=args.phase_only_cycles,
    )


if __name__ == "__main__":
    main()
