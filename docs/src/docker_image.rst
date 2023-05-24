.. _docker:

************
Docker image
************

The pipeline currently uses
`WSClean <https://wsclean.readthedocs.io/en/latest/index.html>`_ and
`DP3 <https://dp3.readthedocs.io/en/latest/>`_ to make images,
generate model visibilities from them, and perfom calibration against the
models.

The Dockerfile below can be used to build an image containing both WSClean
and DP3, and all the required dependencies.
This is based on the Dockerfile recipe given for Ubuntu 20.04 at
`<https://github.com/lofar-astron/DP3/blob/master/docker/ubuntu_20_04_base>`_,
with build commands for WSClean and DP3 added at the end.

.. warning::

    This image contains the MPI-enabled version of the WSClean
    executable ``wsclean-mp``. A code patch is applied during
    the build process: the maximum MPI message size it uses is reduced
    from 2GB to 1GB, in order to work around a limitation of the network
    interfaces on CSD3 icelake nodes, which do not allow messages larger than
    1GB.

Obtaining a docker image
========================

To build the image with the aforementioned patch applied, navigate to the base
directory of the repository from a terminal window and run:

.. code-block::

    cd docker/
    docker build -f Dockerfile --tag <MY_IMAGE_TAG> .

Alternatively, a pre-built image is currently available to download from
DockerHub with the name ``vmorello/dp3-wsclean-mpi``

.. code-block::

    docker pull vmorello/dp3-wsclean-mpi:latest


Building a singularity image
============================

To build a *singularity* image based on this docker image, there are two main
solutions. If working on a compute facility, you likely won't have access to
the docker daemon, and thus won't be allowed to build docker images locally.
The solution is to refer to an image on DockerHub:

.. code-block::

    singularity build dp3-wsclean-mpi.sif docker://vmorello/dp3-wsclean-mpi:latest

The above command will create a ready-to-use singularity image file named
``dp3-wsclean-mpi.sif``.

If building docker images locally is allowed, there is the option of referring
to said local docker image as follows:

.. code-block::

    singularity build dp3-wsclean-mpi.sif docker-daemon://dp3-wsclean-mpi:latest


Dockerfile
==========

.. literalinclude:: ../../docker/Dockerfile
