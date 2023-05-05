# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## 0.2.2 - 2023-05-05

### Added

- The pipeline will now run `wsclean-mp` distributed on multiple nodes if executed in a SLURM environment and if multiple nodes have been allocated. Otherwise, it runs the regular `wsclean`.
- Dockerfile with MPI-enabled WSClean, where WSClean has been patched so that it chunks its large MPI messages into 1 GB pieces (instead of 2 GB, the official maximum MPI message size). This is to work around an issue with the network interfaces on CSD3 nodes that refuse to send 1 GB+ MPI messages.


## 0.2.1 - 2023-05-05

### Added

- Can now process input data split into multiple measurement sets, where each holds one distinct sub-band. Before processing actually starts, the input data are copied and merged into a single, temporary measurement set, on which self-calibration is then performed in-place.

### Changed

- In the pipeline app, input measurement set(s) must now be provided via the required command-line option `--input-ms`, instead of a positional argument.


## 0.2.0 - 2023-04-30

Intermediate release in PI18. While the self-calibration logic remains identical to `v0.1.0`, the code has been fully re-architected to be easily run on CSD3, unit testable, and extended in future iterations.

### Added

- Unit tests.
- Logging.
- Made the code into a proper Python package. Once installed, the pipeline app is accessible in a terminal from anywhere via the command `mid-selfcal-pipeline`.
- Real-time capture of stdout/stderr lines emitted by wsclean and DP3, which are redirected into the pipeline's Python logger.
- When launched, the pipeline creates a unique output sub-directory for the current run, inside which all temporary and output files are written, including the logs as `logfile.txt`. 
- Graceful termination when receiving `SIGINT` or `SIGTERM`.
- Guaranteed removal of intermediate output and temporary files on exit, successful or not.
- Exposed more wsclean parameters via the pipeline's command line: `--size` and `--scale`, which control the output image dimensions and angular pixel scale, respectively.

### Changed

- Both wsclean and DP3 are now run inside singularity containers, which makes the pipeline portable between computing facilities; compiling DP3 and wsclean on bare metal can be a headache (especially wsclean with MPI support). Consequently, the pipeline app now requires to be passed a singularity image file that provides both DP3 and wsclean via `--singularity-image`.
- wsclean is now instructed to write its temporary files in the designed output directory rather than in the same directory as the input measurement set.

### Removed

- Previous pipeline app `selfcal_di.py`.


## 0.1.0 - 2023-03-24

Initial release created in PI17.
