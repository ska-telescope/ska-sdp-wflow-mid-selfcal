FROM ubuntu:20.04

# TODO: needs to be bumped before next DP3 release
# ENV IDG_VERSION=0.8

# This is casacore v3.5 (July 2022)
ENV CASACORE_VERSION=ff766c49fdfddd34715fd017a08aaedcc01736e0
ENV EVERYBEAM_VERSION=d39301d475298321b3aa7de765ca75f325311d2c
ENV IDG_VERSION=6b61c038883ad3f807d20047c4f9e1a1f0b8d98a
ENV AOFLAGGER_VERSION=65d5fba4f4c12797386d3fd9cd76734956a8b233
ENV WSCLEAN_VERSION=a499367a
ENV DP3_VERSION=337c784a31d8fb59f6c4707c298006f2eb6c7583

# NOTE: adding libopenmpi-dev means that wsclean-mp gets built automatically
RUN export DEBIAN_FRONTEND="noninteractive" && \
    apt-get update && \
    apt-get install -y \
        bison \
        build-essential \
        cmake \
        doxygen \
        flex \
        gfortran \
        git \
        libarmadillo-dev \
        libboost-date-time-dev \
        libboost-filesystem-dev \
        libboost-program-options-dev \
        libboost-python-dev \
        libboost-system-dev \
        libboost-test-dev \
        libcfitsio-dev \
        libfftw3-dev \
        libgsl-dev \
        libgtkmm-3.0-dev \
        libhdf5-serial-dev \
        liblua5.3-dev \
        libopenmpi-dev \
        libpng-dev \
        ninja-build \
        pkg-config \
        pybind11-dev \
        python3-dev \
        python3-numpy \
        python3-pip \
        wcslib-dev \
        wget \
    && \
    rm -rf /var/lib/apt/lists/*

# Build casacore
RUN mkdir /casacore && cd /casacore \
    && git clone https://github.com/casacore/casacore.git src \
    && ( cd src/ && git checkout ${CASACORE_VERSION} ) \
    && mkdir build && cd build \
    && cmake -DUSE_READLINE=NO -DBUILD_TESTING=OFF -DCMAKE_INSTALL_PREFIX=/usr ../src \
    && make -j4 install \
    && cd / && rm -rf casacore

# Build aoflagger3
RUN mkdir /aoflagger && cd /aoflagger \
    && git clone https://gitlab.com/aroffringa/aoflagger.git src \
    && ( cd src/ && git checkout ${AOFLAGGER_VERSION} ) \
    && mkdir build && cd build \
    && cmake -G Ninja -DCMAKE_INSTALL_PREFIX=/usr ../src \
    && ninja install \
    && cd / && rm -rf aoflagger

# Build IDG
# (PORTABLE: it may run on a different node than where it was compiled)
RUN mkdir /idg && cd /idg \
    && git clone https://git.astron.nl/RD/idg.git src \
    && ( cd src/ && git checkout ${IDG_VERSION} ) \
    && mkdir build && cd build \
    && cmake -G Ninja -DCMAKE_INSTALL_PREFIX=/usr -DPORTABLE=ON ../src \
    && ninja install \
    && cd / && rm -rf idg

# Build EveryBeam
RUN mkdir /everybeam && cd /everybeam \
    && git clone https://git.astron.nl/RD/EveryBeam.git src \
    && ( cd src/ && git checkout ${EVERYBEAM_VERSION} ) \
    && mkdir build && cd build \
    && cmake -G Ninja -DCMAKE_INSTALL_PREFIX=/usr ../src -DPYTHON_EXECUTABLE=/usr/bin/python3 \
    && ninja install \
    && cd / && rm -rf everybeam

# Install pip dependencies
RUN pip3 install \
    autosemver==0.5.5 \
    gcovr \
    h5py \
    jsonschema2rst==0.1.0 \
    sphinx \
    sphinx-rtd-theme

# Build DP3
RUN mkdir /dp3 && cd /dp3 \
    && git clone https://git.astron.nl/RD/DP3.git src \
    && cd src \
    && git checkout ${DP3_VERSION} \
    && git submodule update --init --recursive \
    && mkdir build && cd build \
    && cmake -DCMAKE_INSTALL_PREFIX=/usr .. \
    && make -j4 install \
    && cd / && rm -rf dp3
ENV PYTHONPATH=/usr/local/lib/python3.8/site-packages

# Build WSClean
RUN mkdir /wsclean && cd /wsclean \
    && git clone https://gitlab.com/aroffringa/wsclean.git src \
    && cd src \
    && git checkout ${WSCLEAN_VERSION} \
    && git submodule update --init --recursive

# HACK: Apply patch that lowers the limit on the maximum MPI message size
# inside wsclean, from 2 GB to 1 GB.
COPY mpibig.cpp /wsclean/src/distributed/mpibig.cpp

RUN cd /wsclean \
    && mkdir build && cd build \
    && cmake -G Ninja -DCMAKE_INSTALL_PREFIX=/usr ../src \
    && ninja install \
    && cd / && rm -rf wsclean

# Install WSRT Measures (extra casacore data, for integration tests)
# Note: The file on the ftp site is updated daily. When warnings regarding leap
# seconds appear, ignore them or regenerate the docker image.
RUN wget -nv -O /WSRT_Measures.ztar ftp://ftp.astron.nl/outgoing/Measures/WSRT_Measures.ztar \
    && mkdir -p /usr/share/casacore/data \
    && cd /usr/share/casacore/data \
    && tar xfz /WSRT_Measures.ztar \
    && rm /WSRT_Measures.ztar
