import argparse
import os
from math import ceil

import matplotlib.pyplot as plt
import numpy as np
from astropy.io import fits
from numpy.typing import NDArray


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments into a convenient object.
    """
    parser = argparse.ArgumentParser(
        description="Convert WSClean FITS files to PNG",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-r",
        "--reduction",
        type=str,
        choices=("sum", "max"),
        default="sum",
        help=(
            "Reduction function to apply to shrink the image size on a "
            "NxN cell-by-cell basis."
        ),
    )
    parser.add_argument(
        "--zmin",
        type=float,
        default=-4.0,
        help=(
            "Minimum colormap value in units of the estimated background "
            "noise standard deviation."
        ),
    )
    parser.add_argument(
        "--zmax",
        type=float,
        default=+10.0,
        help=(
            "Maximum colormap value in units of the estimated background "
            "noise standard deviation."
        ),
    )
    parser.add_argument(
        "files",
        nargs="+",
        type=os.path.abspath,
        help="WSClean FITS files.",
    )
    return parser.parse_args()


def _crop_reshape_data_4d(data: NDArray, factor: int) -> NDArray:
    """
    Given `data` with shape (X, Y), reshape it to (X // N, N, Y // N, N) so
    that it's ready to have its resolution reduced by N = `factor`. Both
    dimensions of the 2D array are cropped down to the nearest multiple N.
    """
    rows, cols = data.shape
    rows_out = rows // factor
    cols_out = cols // factor
    rows_in = factor * rows_out
    cols_in = factor * cols_out
    return data[:rows_in, :cols_in].reshape(rows_out, factor, cols_out, factor)


def _max_shrink(data: NDArray, factor: int) -> NDArray:
    return _crop_reshape_data_4d(data, factor).max(axis=(1, 3))


def _sum_shrink(data: NDArray, factor: int) -> NDArray:
    return _crop_reshape_data_4d(data, factor).sum(axis=(1, 3))


def shrink(data, factor, reduction: str = "sum") -> NDArray:
    """
    Shrink a 2D array by `factor`, applying the chosen reduction operation on
    a NxN cell-by-cell basis where N = factor. Both dimensions of the 2D array
    are cropped down to the nearest multiple N.
    """
    functions = {
        "sum": _sum_shrink,
        "max": _max_shrink,
    }
    func = functions[reduction]
    return func(data, factor)


def _colormap_bounds(
    data: NDArray, zmin: float = -4.0, zmax: float = +10.0
) -> tuple[float, float]:
    q_1, med, q_3 = np.percentile(data.ravel(), (25, 50, 75))
    iqr = q_3 - q_1

    # NOTE: model images often contain a vast majority of zeros, in which case
    # the stddev robust estimator based on the IQR is zero. In this case,
    # we fall back to regular stddev.
    stddev = iqr / 1.349 if iqr > 0 else data.std()
    vmin = med + zmin * stddev
    vmax = med + zmax * stddev
    return vmin, vmax


def _figure_from_data(
    data: NDArray,
    reduction: str = "sum",
    zmin: float = -4.0,
    zmax: float = +10.0,
):
    npix_max = 4000
    shrink_factor = ceil(max(*data.shape) / npix_max)
    data = shrink(data, shrink_factor, reduction)
    vmin, vmax = _colormap_bounds(data, zmin, zmax)
    fig = plt.figure(figsize=(20, 20), dpi=100)
    plt.imshow(data, vmin=vmin, vmax=vmax, origin="lower")
    plt.xticks([])
    plt.yticks([])
    return fig


def _figure_from_fits(
    fits_fname: str,
    reduction: str = "sum",
    zmin: float = -4.0,
    zmax: float = +10.0,
):
    with fits.open(fits_fname) as hdu_list:
        hdu = hdu_list[0]

        # pylint: disable=no-member
        # NOTE: data is 4-dimensional, X and Y are the last axes. This assumes
        # there is only one pol and one freq channel in the image cube.
        imgdata = hdu.data[0, 0]
        return _figure_from_data(
            imgdata, reduction=reduction, zmin=zmin, zmax=zmax
        )


def main():
    """
    Entry point for fits2png app.
    """
    plt.switch_backend("Agg")
    args = parse_args()
    for fname in args.files:
        print(f"Processing: {fname}")
        basename, __ = os.path.splitext(fname)
        png_name = f"{basename}.png"
        fig = _figure_from_fits(
            fname,
            reduction=args.reduction,
            zmin=args.zmin,
            zmax=args.zmax,
        )
        fig.savefig(png_name, bbox_inches="tight")
        plt.close(fig)


if __name__ == "__main__":
    main()
