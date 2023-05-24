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

    $ mid-selfcal-fits2png --help
    usage: mid-selfcal-fits2png [-h] files [files ...]

    Convert WSClean FITS files to PNG

    positional arguments:
    files       WSClean FITS files.

    optional arguments:
    -h, --help  show this help message and exit

It can be called on multiple files at once as follows:

.. code-block::

    $ cd <PIPELINE_OUTPUT_DIR>
    $ mid-selfcal-fits2png *.fits

For each FITS file, it will create in the same directory an identically-named
image with a ``.png`` extension, with a reduced resolution of
2000 x 2000 pixels. Original-resolution images are shrunk via a max-pooling
operation to preserve the faint sources. The colour scale is dynamically
adjusted based on a robust estimation of the background noise. Typical run
times are 10 to 60 seconds per FITS file, depending on their pixel size.
