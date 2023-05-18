# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## 0.2.5 - 2023-05-18

This version fixes a major issue with DP3 where gaincal would indefinitely freeze on startup on some of the AA2 datasets. The problem would trigger when DP3 was running with 64 or more CPUs available; the fix is to specify 63 threads or less via the `numthreads` DP3 parameter.

### Fixed

- Fixed the DP3 gaincal freeze problem by always setting the number of DP3 gaincal threads to 16.
- In `selfcal_pipeline()`, changed the default value of `clean_iters` to match that of the pipeline app.

### Added

- FITS to PNG command-line plotting app `mid-selfcal-fits2png`, which is quite useful to check selfcal progress without having to download 2GB+ FITS files.
- Added `numpy`, `matplotlib` and `astropy` as dependencies as a result of the above.
- Pipeline now automatically removes intermediate FITS files created by `wsclean-mp` just after it finishes running, and also on pipeline exit (sucessful or not).

### Changed

- Dockerfile: now building casacore v3.5 from source instead of using the casacore Ubuntu packages which are older (v3.2). Explicitly pin casacore and DP3 versions.


## 0.2.4 - 2023-05-11

This version contains minor improvements to make benchmarking easier.

### Added

- Pipeline app now logs the exact arguments with which it was called.
- If running in a SLURM environment, the allocated compute resources are now logged before starting self-calibration: number of nodes, number of CPUs, amount of memory. The latter does not work reliably on CSD3 due to its SLURM scheduler not always setting the env variable `$SLURM_MEM_PER_NODE`.
- The total bytesize of the input data is now logged before starting self-calibration.
- It is now possible to provide an empty list to `--clean-iters`, which results in directly imaging the data without any self-calibration cycles.
- It is now possible to provide an empty list to `--phase-only-cycles` as well.

### Changed

- Altered the definition of the `--clean-iters` argument. It still represents the number of deconvolution iterations to perform in each self-cal cycle, but now excludes the final imaging step, whose number of iterations is now hardcoded to 1 million (effectively, that means cleaning down to the noise). The number of actual self-cal cycles is now equal to the length of the `--clean-iters` list.


## 0.2.3 - 2023-05-10

### Added

- Can now perform an initial calibration step before starting the self-calibration loop. This can be done by providing a file in sourcedb format via the optional argument `--initial-sky-model`.
- Two DP3 gaincal parameters can now be tweaked from the command line via the optional arguments `--gaincal-solint` and `--gaincal-nchan`. The values provided are common to all calibration stages, including the optional initial calibration. If not provided, the DP3 default values are used.

### Changed

- `gaincal.tolerance` is now `1e-3` in all calibration stages, instead of the default `1e-5`.


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
