.. _installation:

************
Installation
************


Creating the DP3 / WSClean singularity image
============================================

The pipeline runs DP3 and WSClean inside a singularity container. A requirement
is thus to build a singularity image file that allows to run them both.

Please follow the instructions on the :ref:`docker` page.


Installing the pipeline
=======================

A **highly** recommended first step is to create an isolated Python environment in
which to install the pipeline's Python module. There are several ways of doing
this, so feel free to choose your favourite.
Here we will use ``conda`` because that is often
the environment manager of choice when working on supercomputing facilities.

The pipeline requires Python version 3.9 or higher. Below we create a new
conda environment called ``selfcal``, activate it, then inside it we install
the official package manager of SKAO: ``poetry``.

.. code-block::

    conda create --name selfcal python=3.9
    conda activate selfcal
    pip install poetry

    
**NOTE:** Installing ``poetry`` via ``conda`` was broken at the time of
writing, which is why we use ``pip`` above.

Then, navigate to the base directory where you wish to clone the repository and
run:

.. code-block::

    git clone --recurse-submodules https://gitlab.com/ska-telescope/sdp/science-pipeline-workflows/ska-sdp-wflow-mid-selfcal


Lastly, install the module:

.. code-block::

    cd ska-sdp-wflow-mid-selfcal/
    poetry install

The ``poetry install`` command does the equivalent of pip's editable install,
meaning that you may freely edit the code and see the changes in action next
time the pipeline code is run.

Once the installation is complete, the pipeline command-line app should be
accessible from anywhere when inside your newly created Python environment.
Type the following command to check it all works:

.. code-block::

    mid-selfcal-pipeline --help
