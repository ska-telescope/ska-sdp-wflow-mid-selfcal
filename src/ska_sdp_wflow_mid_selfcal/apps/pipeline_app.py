import argparse
import os
from pathlib import Path

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
        type=Path,
        default=None,
        help=(
            "Optional path to a singularity image file with both WSClean "
            "and DP3 installed. If specified, run WSClean and DP3 inside "
            "singularity containers; otherwise, run them on bare metal."
        ),
    )
    parser.add_argument(
        "--base-outdir",
        type=Path,
        default=Path.cwd(),
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
        "--weight",
        nargs="+",
        type=str,
        # NOTE: the code expects this argument to be a list of strings
        default=["uniform"],
        help=(
            "Weighting mode, either 'natural', 'uniform' or briggs <R>', "
            "where `R` is the Briggs robustness parameter, a real-valued "
            "number between -2.0 and 2.0. "
        ),
    )
    parser.add_argument(
        "--initial-sky-model",
        type=Path,
        help=(
            "Optional path to a DP3 sky model file to use for an initial "
            "calibration, before the self-cal starts."
        ),
    )
    parser.add_argument(
        "--gaincal-solint",
        type=int,
        default=1,
        help=(
            "gaincal.solint parameter for DP3: number of time slots over "
            "which a solution is assumed to be constant"
        ),
    )
    parser.add_argument(
        "--gaincal-nchan",
        type=int,
        default=0,
        help=(
            "gaincal.nchan parameter for DP3: number of channels over "
            "which a solution is assumed to be constant"
        ),
    )
    parser.add_argument(
        "--clean-iters",
        nargs="*",
        type=int,
        default=[20, 100, 500],
        help=(
            "Maximum Clean iterations per self-cal cycle, as a list of "
            "integers. This does not include the final imaging stage, "
            "where the image is deconvolved down to the noise floor. To run "
            "only the final imaging stage without selfcal, specify "
            "this argument without a value."
        ),
    )
    parser.add_argument(
        "--final-clean-iters",
        type=int,
        default=100_000,
        help=("Maximum Clean iterations for the final imaging stage."),
    )
    parser.add_argument(
        "--phase-only-cycles",
        nargs="*",
        type=int,
        default=[0],
        help=(
            "List of self-cal cycle indices (zero-based) in which to perform "
            "phase-only calibration. A reasonable default is to run a "
            "phase-only calibration for the first cycle. To avoid doing any "
            "phase-only cal cycles, specify this argument without a value. "
        ),
    )
    parser.add_argument(
        "--input-ms",
        nargs="+",
        required=True,
        type=Path,
        help="Input measurement set(s).",
    )
    return parser.parse_args()


def main():
    """
    Entry point for the selfcal pipeline app.
    """
    args = parse_args()
    outdir = create_pipeline_output_subdirectory(args.base_outdir)
    logfile_path = outdir / "logfile.txt"
    setup_logging(logfile_path)

    LOGGER.info("Called with arguments:")
    for key, val in vars(args).items():
        LOGGER.info(f"    {key}: {val}")

    LOGGER.info(f"Created output directory: {outdir!r}")
    selfcal_pipeline(
        args.input_ms,
        outdir=outdir,
        singularity_image=args.singularity_image,
        size=args.size,
        scale=args.scale,
        weight=" ".join(args.weight),
        initial_sky_model=args.initial_sky_model,
        gaincal_solint=args.gaincal_solint,
        gaincal_nchan=args.gaincal_nchan,
        clean_iters=args.clean_iters,
        final_clean_iters=args.final_clean_iters,
        phase_only_cycles=args.phase_only_cycles,
    )


if __name__ == "__main__":
    main()
