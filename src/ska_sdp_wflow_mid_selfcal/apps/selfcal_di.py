"""
Runs a direction-independent self-calibration loop using
DP3 (gaincal) and WSClean.

Example usage:

python3 selfcal_di.py \
    --clean_iters="20,100,500,500000" \
    --phase_only_cycles="0" \
    --wsclean_extra_params="-size 16384 16384 -scale 1asec -parallel-deconvolution 2500 -gridder wgridder" \
    v12p1_actual_ical_TGcal_900s.ms selfcal_out
"""  # noqa: E501, pylint: disable=line-too-long

import argparse
import subprocess
import sys
import time
from datetime import datetime


def run_app(name, args, stage, log_file):
    """Run a command-line application with supplied arguments.

    Standard output from the process will be captured to the log file,
    and the run time of the process will also be recorded.

    Args:
        name (str): Name of application binary to run.
        args (List(str)): List of command line arguments for the application.
        stage (str): Name of current pipeline stage.
        log_file (file object): Handle to open log file.
    """
    log_file.write("\n" + ("#" * 40) + "\n")
    log_file.write(f"#### Running {name} [{stage}]\n")
    log_file.flush()
    start_time = time.time()
    return_code = subprocess.call(
        [name] + args, stdout=log_file, stderr=subprocess.STDOUT
    )
    if return_code != 0:
        raise RuntimeError(f"{name} exited with code {return_code}")
    log_file.write(f"#### {name} took {time.time() - start_time} seconds\n")
    log_file.write(("#" * 40) + "\n")
    log_file.flush()


def main():
    """
    Entry point for the pipeline.
    """
    # Define command line arguments.
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-n",
        "--clean_iters",
        type=str,
        default="20,100,500,500000",
        help="Maximum Clean iterations per self-cal cycle, as a quoted list. "
        "The number of calibration cycles is one less than the length of the "
        "list, as the final value is used to make the image after the last "
        "calibration.",
    )
    parser.add_argument(
        "-p",
        "--phase_only_cycles",
        type=str,
        default="0",
        help="Comma-separated list of self-cal cycle indices (zero-based) "
        "in which to perform phase-only calibration. "
        "The default is to run a phase-only calibration for the first cycle.",
    )
    parser.add_argument(
        "-s",
        "--initial_sky_model",
        type=str,
        help="Optional path to a DP3 sky model file to use for an initial "
        "calibration, before the self-cal starts.",
    )
    parser.add_argument(
        "-w",
        "--wsclean_extra_params",
        type=str,
        required=True,
        help="Extra parameters for WSClean (e.g. image size and pixel scale). "
        "Apart from the input and output names, the only ones set by "
        "this script are -niter, -mgain (0.8), and -auto-threshold (3).",
    )
    parser.add_argument("ms_in", help="name of input Measurement Set")
    parser.add_argument("image_out", help="name of output FITS image")

    # Get command line arguments.
    args = parser.parse_args()
    initial_sky_model = args.initial_sky_model
    clean_iters = [int(item) for item in args.clean_iters.split(",")]
    phase_only = [int(item) for item in args.phase_only_cycles.split(",")]
    num_loops = len(clean_iters) - 1
    wsclean_extras = args.wsclean_extra_params.split(" ")
    ms_in = args.ms_in
    image_out = args.image_out

    # Open a log file.
    log_file_name = datetime.now().strftime("self-cal_%Y-%m-%dT%H%M%S.txt")
    # pylint: disable=consider-using-with
    log_file = open(log_file_name, "w", encoding="utf-8")
    log_file.write(f"Self-cal pipeline starting at {datetime.now()}\n")
    log_file.write("Command line arguments:\n")
    log_file.write("\n".join(sys.argv[1:]))
    log_file.flush()

    # Set pointer to next Measurement Set to use.
    next_ms_to_use = ms_in

    if initial_sky_model:
        # Run DP3 to do an initial calibration.
        args = [
            f"msin={next_ms_to_use}",
            "msout=calibrated.ms",
            "msout.overwrite=true",
            "steps=[gaincal]",
            "gaincal.caltype=diagonal",
            "gaincal.maxiter=50",
            "gaincal.solint=1",
            "gaincal.nchan=0",
            "gaincal.tolerance=1e-3",
            "gaincal.propagatesolutions=false",
            "gaincal.usebeammodel=true",
            "gaincal.usechannelfreq=true",
            "gaincal.applysolution=true",
            f"gaincal.sourcedb={initial_sky_model}",
            "gaincal.parmdb=solutions_initial.h5",
        ]
        run_app("DP3", args, "initial calibration", log_file)
        next_ms_to_use = "calibrated.ms"

    # Iterate over self-cal cycles.
    for i_loop in range(num_loops):
        stage = f"cycle {i_loop + 1}/{num_loops}"

        # Run WSClean with the number of clean iterations to use for this cycle
        # Predicted visibilities will be written out into the MODEL_DATA column
        # fmt: off
        args = [
            "-auto-threshold", "3",
            "-niter", str(clean_iters[i_loop]),
            "-mgain", "0.8",
            "-name", f"temp_image_cycle_{i_loop}",
        ]
        # fmt: on
        args += wsclean_extras
        args += [next_ms_to_use]
        run_app("wsclean", args, stage, log_file)

        # Use phase-only calibration for the specified iteration(s).
        cal_type = "diagonalphase" if i_loop in phase_only else "diagonal"

        # Run DP3 using the model written by WSClean.
        args = [
            f"msin={next_ms_to_use}",
            "msout=calibrated.ms",
            "msout.overwrite=true",
            "steps=[gaincal]",
            f"gaincal.caltype={cal_type}",
            "gaincal.maxiter=50",
            "gaincal.usemodelcolumn=true",
            "gaincal.applysolution=true",
        ]
        run_app("DP3", args, stage, log_file)
        next_ms_to_use = "calibrated.ms"

    # Run WSClean to make the final image.
    # fmt: off
    args = [
        "-auto-threshold", "3",
        "-niter", str(clean_iters[-1]),
        "-mgain", "0.8",
        "-name", image_out,
    ]
    # fmt: on
    args += wsclean_extras
    args += [next_ms_to_use]
    run_app("wsclean", args, "final image", log_file)

    # Close the log.
    log_file.close()


if __name__ == "__main__":
    main()
