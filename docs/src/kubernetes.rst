.. _kubernetes:

***********************
Running with Kubernetes
***********************

After setting up a local Kubernetes installation to use the
`Data Processing Testing Platform <https://confluence.skatelescope.org/display/SWSI/Data+Processing+Testing+Platform>`_,
copy the Python script and the input Measurement Set to a persistent
(shared or private) directory on the remote cluster, which should be created
first if necessary.
Copying the input data and script will require the use of the command
``kubectl cp`` to perform the copy operation.

The pipeline can then be run as a Kubernetes job using the shell script below,
specifying the following three named parameters, which can use either the
single-character or long names. A double-dash ``--`` separates these from
the command to run inside the container, which should be ``python3`` and the
name of the Python script, with its own command line arguments):

- ``-d|--jobdir``: The full path to the working directory on the remote system.

- ``-n|--namespace``: The Kubernetes namespace to use for your account.

- ``-i|--image``: The name of the Docker image to run.

- ``-- python3 selfcal_di.py <args>``: The command to run in the container.

Download the shell script here:
:download:`kubectl_run.sh <../../scripts/kubectl_run.sh>`

.. literalinclude:: ../../scripts/kubectl_run.sh
