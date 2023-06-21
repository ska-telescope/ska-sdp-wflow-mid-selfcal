.. _additional_apps:

***************
Additional Apps
***************


WSClean FITS to PNG converter
=============================

As part of pipeline runs, WSClean produces a number of FITS images that it is
interesting to visually inspect, for example to verify that the
self-calibration process is converging. However, FITS files tend to have be
quite bulky (2GB+) and take a long time to download from a remote computing
facility in order to display them with dedicated software such as DS9.

To circumvent that problem, an app that converts high-resolution FITS to more
manageably-sized PNG files is included in the repository and automatically
installed with the pipeline Python module:

.. code-block::

    usage: mid-selfcal-fits2png [-h] [-r {sum,max}] [--zmin ZMIN] [--zmax ZMAX] files [files ...]

    Convert WSClean FITS files to PNG

    positional arguments:
    files                 WSClean FITS files.

    optional arguments:
    -h, --help            show this help message and exit
    -r {sum,max}, --reduction {sum,max}
                            Reduction function to apply to shrink the image size on a NxN cell-by-cell basis. (default: sum)
    --zmin ZMIN           Minimum colormap value in units of the estimated background noise standard deviation. (default: -4.0)
    --zmax ZMAX           Maximum colormap value in units of the estimated background noise standard deviation. (default: 10.0)


It can be called on multiple files at once as follows:

.. code-block::

    $ cd <PIPELINE_OUTPUT_DIR>
    $ mid-selfcal-fits2png *.fits

For each FITS file, it will create in the same directory an identically-named
image with a ``.png`` extension, with a reduced resolution of
2000 x 2000 pixels. Original-resolution images are shrunk by the appropriate
integer factor N, by applying a reduction function to NxN cells (i.e. taking
their sum or their max value).

The colour scale is dynamically adjusted based on a robust estimation of the
background noise *after* shrinking. Typical run times are 10 to 60 seconds per
FITS file, depending on their pixel size.

.. note::

    Max-pooling was found to excessively enhance some otherwise invisible
    artifacts in some images, and can provide an overall distorted result.
    We have left the option for future reference, but it is highly recommended
    to use the "sum" reduction function.
