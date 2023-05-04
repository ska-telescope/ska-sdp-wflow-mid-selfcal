# Docker build notes

The Infiniband network interfaces on the CSD3 icelake nodes do not support sending MPI messages larger than 1 GB, while the "standard" maximum MPI message size is 2 GB. WSClean internally breaks down large MPI messages into 2 GB chunks, the code that does this in the WSClean code base lies in `distributed/mpibig.cpp`. Consequently, `wsclean-mp` crashes on CSD3 when producing images larger than about 10K x 10K.

As a temporary fix, we build a docker image with a modified `mpibig.cpp` file where messages are split into 1 GB chunks instead. To build the Dockerfile:
```
cd docker/
docker build -f Dockerfile-MPI --tag <MY_IMAGE_TAG> .
```