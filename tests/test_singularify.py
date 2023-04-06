from ska_sdp_wflow_mid_selfcal.singularify import singularify


def test_singularify_given_wsclean_command():
    """
    Self-explanatory.
    """
    command = [
        "wsclean",
        "-size",
        "4096",
        "4096",
        "-name",
        "/output/wsclean",
        "/data/input.ms",
    ]
    image = "wsclean.sif"
    expected_result = [
        "singularity",
        "exec",
        "--bind",
        "/output:/mnt/output",
        "--bind",
        "/data:/mnt/data",
        image,
        "wsclean",
        "-size",
        "4096",
        "4096",
        "-name",
        "/mnt/output/wsclean",
        "/mnt/data/input.ms",
    ]
    assert expected_result == singularify(command, image)


def test_singularify_given_dp3_command():
    """
    Check whether absolute paths provided in the form `{PARAM}={ABSPATH}` are
    detected and processed correctly.
    """
    command = [
        "DP3",
        "steps=[gaincal]",
        "msin=/data/input.ms",
        "msout=/output/calibrated.ms",
        "gaincal.applysolution=true",
    ]
    image = "DP3.sif"
    expected_result = [
        "singularity",
        "exec",
        "--bind",
        "/data:/mnt/data",
        "--bind",
        "/output:/mnt/output",
        image,
        "DP3",
        "steps=[gaincal]",
        "msin=/mnt/data/input.ms",
        "msout=/mnt/output/calibrated.ms",
        "gaincal.applysolution=true",
    ]
    assert expected_result == singularify(command, image)


def test_singularify_given_command_with_repeated_directory():
    """
    Make sure no repeated bind mount points are generated.
    """
    command = ["touch", "/data/file1", "/data/file2"]
    image = "ubuntu.sif"
    expected_result = [
        "singularity",
        "exec",
        "--bind",
        "/data:/mnt/data",
        image,
        "touch",
        "/mnt/data/file1",
        "/mnt/data/file2",
    ]
    assert expected_result == singularify(command, image)
