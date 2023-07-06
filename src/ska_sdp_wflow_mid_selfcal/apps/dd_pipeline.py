import argparse
from pathlib import Path

from ska_sdp_wflow_mid_selfcal import __version__
from ska_sdp_wflow_mid_selfcal.apps.dd_pipeline_app2 import selfcal_pipeline_dd


def _default_config_path() -> Path:
    return Path(__file__).parent / "dd_pipeline_config.yml"


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments into a convenient object.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Launch the SKA Mid direction-dependent self-calibration pipeline"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument(
        "--config",
        type=Path,
        default=_default_config_path(),
        help=(
            "Path to configuration file. "
            "Use the default configuration file if unspecified."
        ),
    )
    parser.add_argument(
        "--sky-model",
        type=Path,
        required=True,
        help="Path to sky model file in sourcedb format.",
    )
    parser.add_argument(
        "--size",
        nargs=2,
        type=int,
        required=True,
        help="Output image size in pixels, as two integers <width> <height>",
    )
    parser.add_argument(
        "--scale",
        type=str,
        required=True,
        help=('Scale of a pixel, as a string such as "20asec" or "0.01deg".'),
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
    args = parse_args()
    print(args)


if __name__ == "__main__":
    main()
