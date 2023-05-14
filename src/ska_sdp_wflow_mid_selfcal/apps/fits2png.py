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
        "files",
        nargs="+",
        type=os.path.abspath,
        help="WSClean FITS files.",
    )
    return parser.parse_args()


def _max_pool_shrink(data: NDArray, factor: int) -> NDArray:
    """
    Shrink a 2D array by `factor`, max-pooling it on a NxN cell-by-cell basis
    where N = factor.
    """
    rows, cols = data.shape
    rows_out = rows // factor
    cols_out = cols // factor
    rows_in = factor * rows_out
    cols_in = factor * cols_out
    return (
        data[:rows_in, :cols_in]
        .reshape(rows_out, factor, cols_out, factor)
        .max(axis=(1, 3))
    )


def _colormap_bounds(
    data: NDArray, zmin: float = -3.0, zmax: float = 8.0
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


def _figure_from_data(data: NDArray):
    npix_max = 4000
    shrink_factor = ceil(max(*data.shape) / npix_max)
    data = _max_pool_shrink(data, shrink_factor)
    vmin, vmax = _colormap_bounds(data)
    fig = plt.figure(figsize=(20, 20), dpi=100)
    plt.imshow(data, vmin=vmin, vmax=vmax, origin="lower")
    plt.xticks([])
    plt.yticks([])
    return fig


def _figure_from_fits(fits_fname: str):
    with fits.open(fits_fname) as hdu_list:
        hdu = hdu_list[0]

        # pylint: disable=no-member
        # NOTE: data is 4-dimensional, X and Y are the last axes. This assumes
        # there is only one pol and one freq channel in the image cube.
        imgdata = hdu.data[0, 0]
        return _figure_from_data(imgdata)


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
        fig = _figure_from_fits(fname)
        fig.savefig(png_name, bbox_inches="tight")
        plt.close(fig)


if __name__ == "__main__":
    main()
