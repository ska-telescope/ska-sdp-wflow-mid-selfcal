import argparse
from pathlib import Path

import yaml

from ska_sdp_wflow_mid_selfcal import __version__
from ska_sdp_wflow_mid_selfcal.apps.dd_pipeline_app2 import selfcal_pipeline_dd, SkyModel


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
            "Path to the selfcal pipeline configuration file. "
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
        "--num-pixels",
        type=int,
        required=True,
        help="Output image size in pixels.",
    )
    parser.add_argument(
        "--pixel-scale",
        type=float,
        required=True,
        help=("Scale of a pixel in arcseconds."),
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

    # TODO: create output directory for pipeline run

    # TODO: setup logger

    with open(args.config, "r") as fobj:
        config_dict = yaml.safe_load(fobj)

    # TODO: load sky model
    sky_model = SkyModel(sources=[])

    selfcal_pipeline_dd(
        args.input_ms,
        sky_model,
        num_pixels=args.num_pixels,
        pixel_scale_asec=args.pixel_scale,
        config_dict=config_dict,
        outdir=Path.cwd(),
    )


if __name__ == "__main__":
    main()
