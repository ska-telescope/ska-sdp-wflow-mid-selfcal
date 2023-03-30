import textwrap

from ska_sdp_wflow_mid_selfcal.slurm_utils import generate_slurm_script


def test_generate_slurm_script():
    """
    Test the slurm script generation process.
    """
    # NOTE: The name of the app is irrelevant for this test. Also, the pipeline
    # entry point, say "mid-selfcal-pipeline" will be expanded to a full path
    # on disk which is environment-dependent. We dodge that problem.
    sys_argv = ["pipeline", "--slurm", "input.ms"]
    outdir = "/data/out_20230101_004242"

    expected_script = f"""
    #!/bin/bash
    #SBATCH --nodes=1
    #SBATCH --tasks-per-node=1
    #SBATCH --mem=32G
    #SBATCH --cpus-per-task=8
    #SBATCH --time=24:00:00
    #SBATCH --partition=skylake
    #SBATCH --output={outdir}/job.out
    #SBATCH --error={outdir}/job.err

    pipeline input.ms
    """
    expected_script = textwrap.dedent(expected_script)
    generated_script = generate_slurm_script(sys_argv, outdir=outdir)
    assert generated_script.strip() == expected_script.strip()
