*********************************
SDP Workflow MID Self-calibration
*********************************

Self-calibration is an iterative process which uses the visibility data to
calibrate itself, building up a more complete model of the sky using
progressively more clean components, as the calibrated visibilities and image
converge towards the true sky.
It relies on the fact that a given array containing `n` antennas has `n`
complex gains to solve for, but with `n * (n - 1) / 2` baseline measurements,
there is enough redundancy to allow this to happen if `n` is large enough.

Typically, self-calibration is done using an initial shallow clean,
finding only the brightest sources in the field to start with.
Model visibilities are generated from these, and used to calibrate the
measured visibility data by solving for sets of complex gains, which are then
applied to generate a corrected data set.
This new data set is then imaged and cleaned a little more deeply, and the
expanded list of clean components is used to generate a more accurate set of
model visibility data.
The process is repeated until the image quality stops improving
(usually after only a few iterations).
The first iteration of the self-calibration cycle may solve only for the
phases, if the cleaning is shallow enough for the source amplitudes to not be
determined sufficiently accurately at that point.
In subsequent iterations, the calibration can proceed by solving for both
amplitude and phase.

This documentation describes how to run the Mid self-calibration pipeline which
implements this self-calibration loop using the LOFAR software components
DP3 and WSClean.

- See the :ref:`installation` page for installation instructions.

- See the :ref:`docker` page for details of the Dockerfile used to
  build the software.

- See the :ref:`pipeline` page for details of the command-line
  arguments used to run it.

- See the :ref:`kubernetes` page for details of how to run the
  pipeline using the Kubernetes environment on the DP Testing Platform.

- See the :ref:`example` page to show the results of a test-run of the pipeline
  using simulated SKA-Mid data.

.. toctree::
  :maxdepth: 1

  installation
  docker_image
  pipeline
  kubernetes
  example
