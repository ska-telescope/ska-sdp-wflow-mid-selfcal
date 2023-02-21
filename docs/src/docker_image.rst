.. _docker:

************
Docker image
************

The pipeline currently uses
`WSClean <https://wsclean.readthedocs.io/en/latest/index.html>`_ and
`DP3 <https://dp3.readthedocs.io/en/latest/>`_ to make images,
generate model visibilities from them, and perfom calibration against the
models.

The following Dockerfile can be used to build an image containing both WSClean
and DP3, and all the required dependencies.
This is based on the Dockerfile recipe given for Ubuntu 20.04 at
`<https://github.com/lofar-astron/DP3/blob/master/docker/ubuntu_20_04_base>`_,
with build commands for WSClean and DP3 added at the end.

A pre-built image is currently available to download from DockerHub with the
name ``fdulwich/dp3-wsclean``.

.. literalinclude:: ../../docker/Dockerfile
