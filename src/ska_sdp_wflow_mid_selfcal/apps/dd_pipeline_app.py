from __future__ import annotations

### Data classes


class MeasurementSet:
    """
    Wrapper for a MS file on disk and its attributed.
    """


class Observation:
    """
    Wrapper for a set of MS files that represent one observations.
    """


def subtract_observations(
    left: Observation, right: Observation
) -> Observation:
    pass


class Field:
    """
    Rectangular area of the sky to be imaged.
    Attributes: imaging centre, image dimensions, pixel scale.
    """


class SkyModel:
    """ """


# NOTE: LOFAR sky model files contain both the list of source parameters and
# the list of patches
class Tesselation:
    """
    Tesselation of the field for DD-calibration purposes.
    """

    def __init__(self) -> None:
        pass

    # NOTE: exact optional arguments TBD. Let's assume we just make a patch
    # around each of the top N brightest sources.
    @classmethod
    def create(
        cls, field: Field, sky_model: SkyModel, num_patches: int
    ) -> Tesselation:
        pass


class TesselatedSkyModel:
    """
    Aggregation of a SkyModel and a Tesselation. This is what a .sourcedb
    file effectively represents.
    """
    def __init__(self, sky_model: SkyModel, tesselation: Tesselation) -> None:
        pass

    @classmethod
    def from_sourcedb(cls, fname: str) -> TesselatedSkyModel:
        pass

    def to_sourcedb(self) -> str:
        pass

    def save_sourcedb(self, fname: str):
        with open(fname, "w") as f:
            f.write(self.to_sourcedb())


class Image:
    pass


def identify_bright_sources(image: Image) -> SkyModel:
    pass


def update_bright_sources_sky_model(orig: SkyModel, new: SkyModel) -> SkyModel:
    pass


class SolutionTable:
    """
    This is what a .h5parm file represents.
    """

    pass


### Operations


# In : MS, Tesselation, SkyModel
# Out: solutions
# Params: type (e.g. slow gain, fast phase ...), solution spans in time and freq,
#     antenna constraints
class Calibration:
    def __init__(
        self, obs: Observation, sky_model: SkyModel, tesselation: Tesselation
    ) -> None:
        pass

    def execute(self) -> tuple[Observation, SolutionTable]:
        pass


# In : MS, Solutions, Tesselation
# Out: Image(s), SkyModel
class Imaging:
    def __init__(
        self,
        obs: Observation,
        solution_table: SolutionTable,
        tesselation: Tesselation,
    ) -> None:
        pass

    def execute(self) -> Image:
        pass


# In : MS (to provide uvw coords), SkyModel, Solutions, Tesselation
# Out: MS with model data
class Prediction:
    def __init__(
        self,
        reference_obs: Observation,
        sky_model: SkyModel,
        tesselation: Tesselation,
        solution_table: SolutionTable,
    ) -> None:
        pass

    def execute(self) -> Observation:
        pass


#
# TODO: How about writing stage classes such that:
# __init__ is passed the tweakable parameters
# execute() is passed the input data that the stage always needs, regardless of other params. E.g. for Prediction it would be: sky model, solution table, ...
#


def dd_selfcal_pipeline(
    obs_in: Observation,
    field: Field,
    calibration_sky_model: SkyModel,
    num_patches: int,
    core_antennas: list[str],
) -> Image:

    bright_sources_sky_model = calibration_sky_model

    # Make Tesselation
    tesselation = Tesselation.create(field, calibration_sky_model, num_patches)

    # Calibrate fast phases
    calibration = Calibration(obs_in, calibration_sky_model, tesselation)
    calibrated_obs, solution_table = calibration.execute()

    # Predict
    prediction = Prediction(
        obs_in, calibration_sky_model, tesselation, solution_table
    )
    calibrated_model_obs = prediction.execute()

    # Subtract model data from input data
    calibrated_subtracted_obs = subtract_observations(
        calibrated_obs, calibrated_model_obs
    )

    # Image
    imaging = Imaging(calibrated_subtracted_obs, solution_table, tesselation)
    image = imaging.execute()

    # Make a sky model from the deconvolved image
    # Then, use it to update the list of bright sources
    filtered_sky_model = identify_bright_sources(image)
    bright_sources_sky_model = update_bright_sources_sky_model(
        bright_sources_sky_model, filtered_sky_model
    )

    # Calibrate slow amplitudes
    # Image

    pass
