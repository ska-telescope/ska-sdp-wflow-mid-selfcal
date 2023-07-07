"""
SkyModel class with methods to load from / save to sourcedb files.

The makesourcedb format specification can be found here:
https://www.astron.nl/lofarwiki/doku.php?id=public:user_software:documentation:makesourcedb
"""
from __future__ import annotations

import math
import re
from collections import OrderedDict
from dataclasses import dataclass
from typing import (
    Callable,
    Literal,
    Match,
    Optional,
    Pattern,
    Sequence,
    Union,
    get_type_hints,
)

import astropy.units as u
from astropy.coordinates import Angle

FieldValue = Union[str, int, float, bool, list[float]]

SI_DELIMITER = ";"


def _parse_spectral_index(text: str) -> list[float]:
    if not (stripped := text.strip("[]")):
        return []
    # NOTE: in the actual file, the delimiter is ",", but we replace that
    # earlier in the parsing process because it creates problems when we try
    # to split the whole line entry on ","
    return list(map(float, stripped.split(SI_DELIMITER)))


def _format_spectral_index(spectral_index: list[float]) -> str:
    csv = ", ".join(str(x) for x in spectral_index)
    return f"[{csv}]"


def _parse_bool(text: str) -> bool:
    if text not in ("true", "false"):
        raise ValueError("Not a valid boolean string representation")
    return text == "true"


def _format_bool(bval: bool) -> str:
    return "true" if bval else "false"


def _parse_mvangle(text: str) -> float:
    """
    Parse MVAngle string to a value in degrees.

    Angles can be given using the MVAngle format, which includes:
    * Sexagesimal HMS format like 12:34:56.78 or 12h34m56.78.
      Note that using colons means hours. It is not allowed to use colons in
      declination values.
    * Sexagesimal DMS format like 12.34.56.78 or 12d34m56.78. Using only points
      means degrees.
    * Floating-point value optionally followed by a unit like 12.34deg or
      12.34rad. If no unit is given, radians are used.
    """
    # astropy's Angle class handles the following out of the box:
    # Angle("1.23deg") -> deg
    # Angle("1.23rad") -> rad
    # Angle("1h23m45.67") -> hourangle
    # Angle("1h23m45.67s") -> hourangle
    # Angle("1d23m45.67") -> deg
    # Angle("1d23m45.67s") -> deg
    #
    # Which means we only need to take care of:
    # "1:23:45.67" -> hourangle
    # "1.23.45.67" -> deg
    chars = set(text)
    if not chars.intersection(set("drh")):
        if ":" in text:
            return Angle(text, unit=u.hourangle).to(u.deg).value

        text = text.replace(".", ":", 2)
        return Angle(text, unit=u.deg).value

    return Angle(text).to(u.deg).value


# Parsing function for each field
FIELD_PARSERS: dict[str, Callable[[str], FieldValue]] = {
    "Name": str,
    "Type": str,
    "Patch": str,
    "Ra": _parse_mvangle,
    "Dec": _parse_mvangle,
    "I": float,
    "SpectralIndex": _parse_spectral_index,
    "LogarithmicSI": _parse_bool,
    "ReferenceFrequency": float,
    "MajorAxis": float,
    "MinorAxis": float,
    "Orientation": float,
}


def _replace_spectral_index_delimiter(line: str) -> str:
    """
    Replace the commas inside the `SpectralIndex` list by something else, so
    that we can later split the line on commas without trouble.
    """
    if "[" not in line:
        return line

    before_si, line = line.split("[", 1)
    spectral_index_str, after_si = line.split("]", 1)
    spectral_index_str = spectral_index_str.replace(",", SI_DELIMITER)
    return "".join((before_si, "[", spectral_index_str, "]", after_si))


def _parse_field_specifier(fspec: str) -> tuple[str, Optional[FieldValue]]:
    """
    Parse a field specifier string such as "Name" or
    "ReferenceFrequency='143489951.1033762'". Returns a tuple
    (name, default_value). If there is no default value for that field,
    return default_value = None.
    """
    items = fspec.split("=")
    if len(items) == 1:
        (name,) = items
        return (name, None)
    name, default_value = items

    # Default values are always enclosed in single quotes
    default_value = default_value.strip("''")
    parser = FIELD_PARSERS[name]
    default_value = parser(default_value)
    return (name, default_value)


def _parse_sourcedb_format_line(
    line: str,
) -> OrderedDict[str, Optional[FieldValue]]:
    """
    Parse the first line of a sourcedb file, which specifies the list of fields
    and optionally, default values for some of them. Example:

    FORMAT = Name, Type, Patch, Ra, Dec, I, SpectralIndex='[]',
        LogarithmicSI, ReferenceFrequency='143489951.1033762',
        MajorAxis, MinorAxis, Orientation

    Fields with default values are specified as <NAME>='<DEFAULT_VALUE>'.

    Returns an OrderedDict {field_name: default_value}, where the order of the
    keys specify the field parsing order; if no default value exists for the
    field, `default_value` is None.
    """
    line = _replace_spectral_index_delimiter(line)

    pattern: Pattern = re.compile(r"(format|FORMAT)(\s*=\s*)(.*)")
    match: Optional[Match] = re.match(pattern, line)
    if match is None:
        raise ValueError("Failed to parse sourcedb format string")

    format_spec_csv = match.group(3)
    field_specifiers = [item.strip() for item in format_spec_csv.split(",")]
    field_specifiers = [
        _parse_field_specifier(fspec) for fspec in field_specifiers
    ]

    default_values = OrderedDict()
    for name, default in field_specifiers:
        default_values[name] = default
    return default_values


def _sourcedb_line_to_dict(
    line: str, default_values_dict: OrderedDict[str, Optional[FieldValue]]
) -> dict[str, Optional[FieldValue]]:
    """
    Parse a single entry of the file into a dictionary.
    The keys in `default_values_dict` provide the order of the fields to be
    parsed in `line`, while its values provide the default values to use for
    missing fields. Default values can be `None`.
    """
    line = _replace_spectral_index_delimiter(line)
    raw_values = [item.strip() for item in line.split(",")]

    result = {}
    for raw_value, (field_name, default_value) in zip(
        raw_values, default_values_dict.items()
    ):
        if raw_value == "" or raw_value.isspace():
            result[field_name] = default_value
        else:
            parser = FIELD_PARSERS[field_name]
            result[field_name] = parser(raw_value)
    return result


def _float_angles_close(left: float, right: float) -> bool:
    """
    Custom float equality closeness check. In practice, this is to work around
    small numerical errors that arise when parsing coordinates in DD:MM:SS
    format. Thresholds are adjusted to that use case.
    """
    return math.isclose(left, right, rel_tol=0.0, abs_tol=1e-12)


def _float_angle_sequences_close(
    left: Sequence[float], right: Sequence[float]
) -> bool:
    return all(_float_angles_close(va, vb) for va, vb in zip(left, right))


@dataclass
class Shape:
    """
    Parameters for a Gaussian-shaped source. A source with a major axis FWHM
    of zero is considered a point source.

    Args:
        major_fwhm_asec: Major full-width at half-maximum in arcseconds
        minor_fwhm_asec: Minor full-width at half-maximum in arcseconds
        position_angle_deg: Position angle of the major axis, in degrees
            East of North
    """

    major_fwhm_asec: float
    minor_fwhm_asec: float
    position_angle_deg: float

    def __post_init__(self) -> None:
        if not self.major_fwhm_asec >= 0:
            raise ValueError("Major axis FWHM must be >= 0")
        if not self.major_fwhm_asec >= self.minor_fwhm_asec:
            raise ValueError("Major axis FWHM must be >= minor axis FWHM")

    @property
    def is_point(self) -> bool:
        """
        Whether the source is a point source.
        """
        return self.major_fwhm_asec == 0

    @property
    def sourcedb_type(self) -> Literal["POINT", "GAUSSIAN"]:
        """
        String that would describe the type of the source in a sourcedb file.
        """
        return "POINT" if self.is_point else "GAUSSIAN"


@dataclass
class FluxModel:
    """
    Flux parameters for a source. See the WSClean docs for an explanation of
    the meaning of the fields:
    https://wsclean.readthedocs.io/en/latest/component_list.html

    Args:
        stokes_i: Stokes I flux in Jy
        spectral_index: list of coefficients of a logarithmic or ordinary
            polynomial that describe the source flux as a function of
            frequency.
        logarithmic_si: Whether `spectral_index` should be interpreted as a
            list of coefficients for a polynomial in `log(nu/nu_0)`,
            where `nu_0` is the reference frequency (see below).
        reference_frequency_hz: Frequency at which the flux and spectral index
            polynomial expansion coefficients are defined.
    """

    stokes_i: float
    reference_frequency_hz: float
    spectral_index: list[float]
    logarithmic_si: bool


# pylint:disable=too-many-instance-attributes
@dataclass
class Source:
    """
    Data class for source parameters. Points and Gaussians are supported, where
    any source with a major FWHM of zero is considered to be a point.
    """

    name: str
    ra_deg: float
    dec_deg: float
    shape: Shape
    flux_model: FluxModel
    patch: Optional[str]

    # NOTE: We have to customise the equality operator, because when parsing
    # RA/Dec from text format, we may end up with a value that deviates from
    # expectation by a few double-precision epsilons
    def __eq__(self, other: Source) -> bool:
        attrs = get_type_hints(Source)
        angle_keys = ["ra_deg", "dec_deg"]
        other_keys = list(set(attrs.keys()) - set(angle_keys))

        def _values(obj: Source, keys: list[str]) -> list:
            return [getattr(obj, key) for key in keys]

        angle_vals_close = _float_angle_sequences_close(
            _values(self, angle_keys), _values(other, angle_keys)
        )
        other_vals_equal = _values(self, other_keys) == _values(
            other, other_keys
        )
        return other_vals_equal and angle_vals_close


def _make_sourcedb_format_line() -> str:
    return (
        "FORMAT = Name, Type, Patch, Ra, Dec, I, SpectralIndex, "
        "LogarithmicSI, ReferenceFrequency, MajorAxis, MinorAxis, Orientation"
    )


def _source_to_sourcedb_entry(source: Source) -> str:
    shape = source.shape
    flux_model = source.flux_model
    field_values = [
        source.name,
        shape.sourcedb_type,
        source.patch,
        str(source.ra_deg) + "deg",
        str(source.dec_deg) + "deg",
        flux_model.stokes_i,
        _format_spectral_index(flux_model.spectral_index),
        _format_bool(flux_model.logarithmic_si),
        flux_model.reference_frequency_hz,
        shape.major_fwhm_asec,
        shape.minor_fwhm_asec,
        shape.position_angle_deg,
    ]
    return ", ".join(map(str, field_values))


def _source_from_attributes_dict(
    attrs: dict[str, Optional[FieldValue]]
) -> Source:

    shape = Shape(
        major_fwhm_asec=attrs["MajorAxis"],
        minor_fwhm_asec=attrs["MinorAxis"],
        position_angle_deg=attrs["Orientation"],
    )

    # Internally, we consider that any source with a major fwhm of zero is a
    # point. Here we ensure consistency, by considering that the "Type" field
    # overrules the others.
    if attrs["Type"] == "POINT":
        shape.major_fwhm_asec = 0.0
        shape.minor_fwhm_asec = 0.0
        shape.position_angle_deg = 0.0

    flux_model = FluxModel(
        stokes_i=attrs["I"],
        reference_frequency_hz=attrs["ReferenceFrequency"],
        spectral_index=attrs["SpectralIndex"],
        logarithmic_si=attrs["LogarithmicSI"],
    )

    return Source(
        name=attrs["Name"],
        ra_deg=attrs["Ra"],
        dec_deg=attrs["Dec"],
        patch=attrs["Patch"],
        flux_model=flux_model,
        shape=shape,
    )


class SkyModel:
    """
    A class that represents a list of sources.
    """

    def __init__(self, sources: list[Source]) -> None:
        """
        Create a new SkyModel from a list of Source objects.
        """
        self._sources = sources

    @property
    def sources(self) -> list[Source]:
        """
        Returns the list of Sources this SkyModel contains.
        """
        return self._sources

    def _to_sourcedb(self) -> str:
        lines = [_make_sourcedb_format_line()]
        for source in self.sources:
            lines.append(_source_to_sourcedb_entry(source))
        return "\n".join(lines) + "\n"

    def save_sourcedb(self, fname: str) -> None:
        """
        Export the SkyModel in sourcedb format to the given file path.
        """
        with open(fname, "w") as fobj:
            fobj.write(self._to_sourcedb())

    @classmethod
    def _parse_sourcedb(cls, text: str) -> SkyModel:
        """
        Create a SkyModel from the contents of a sourcedb file.
        """
        lines = text.strip().split("\n")
        if not lines:
            return SkyModel([])

        default_values_dict = _parse_sourcedb_format_line(lines[0])

        lines = list(
            filter(
                lambda line: line != ""
                and not line.isspace()
                and not line.startswith("#"),
                lines[1:],
            )
        )
        entries = [
            _sourcedb_line_to_dict(line, default_values_dict) for line in lines
        ]
        # NOTE: Patches are entries without a Name, which we remove here
        source_entries = list(filter(lambda e: e["Name"] is not None, entries))
        sources = [
            _source_from_attributes_dict(entry) for entry in source_entries
        ]
        return cls(sources)

    @classmethod
    def load_sourcedb(cls, fname: str) -> SkyModel:
        """
        Create a SkyModel from a sourcedb file.
        """
        with open(fname, "r") as fobj:
            return cls._parse_sourcedb(fobj.read())
