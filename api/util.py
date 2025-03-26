from __future__ import annotations

from datetime import datetime
from datetime import timezone

from covjson_pydantic.observed_property import ObservedProperty as CovJson_ObservedProperty
from covjson_pydantic.parameter import Parameter as CovJson_Parameter
from covjson_pydantic.reference_system import ReferenceSystem
from covjson_pydantic.reference_system import ReferenceSystemConnectionObject
from covjson_pydantic.unit import Unit as CovJson_Unit
from pydantic import AwareDatetime
from pydantic import TypeAdapter

from data.data import Variable


def create_url_from_request(request) -> str:
    return str(request.base_url) + "collections"


def split_string_parameters_to_list(value: str) -> list[str]:
    return list(map(str.strip, value.split(",")))


def split_raw_interval_into_start_end_datetime(value) -> tuple:
    aware_datetime_type_adapter = TypeAdapter(AwareDatetime)

    start_datetime = datetime.min.replace(tzinfo=timezone.utc)
    end_datetime = datetime.max.replace(tzinfo=timezone.utc)

    if not value:
        return start_datetime, end_datetime

    values = list(v.strip() for v in value.split("/"))

    if len(values) == 1:
        start_datetime = aware_datetime_type_adapter.validate_python(values[0])
        end_datetime = start_datetime
    else:
        if values[0] != "..":
            start_datetime = aware_datetime_type_adapter.validate_python(values[0])
        if values[1] != "..":
            end_datetime = aware_datetime_type_adapter.validate_python(values[1])

    return start_datetime, end_datetime


def datetime_to_iso_string(value: datetime) -> str:
    """Returns the datetime as ISO 8601 string.
    Changes timezone +00:00 to the military time zone indicator (Z).

    Keyword arguments:
    value -- A datetime

    Returns:
    datetime string -- Returns the datetime as an ISO 8601 string with the military indicator.
    """
    if value.tzinfo is None:
        # This sort of replicates the functionality of Pydantic's AwareDatetime type
        raise ValueError("Datetime object is not timezone aware")

    iso_8601_str = value.isoformat()
    tz_offset_utc = "+00:00"
    if iso_8601_str.endswith(tz_offset_utc):
        return f"{iso_8601_str[:-len(tz_offset_utc)]}Z"
    else:
        return iso_8601_str


def get_covjson_parameter_from_variable(var: Variable) -> CovJson_Parameter:
    parameter = CovJson_Parameter(
        id=var.id,
        label={"en": var.long_name},
        observedProperty=CovJson_ObservedProperty(
            id=f"https://vocab.nerc.ac.uk/standard_name/{var.standard_name}",
            label={"en": var.standard_name},
        ),
        unit=CovJson_Unit(label={"en": var.units}),
    )
    return parameter


def get_reference_system() -> list[ReferenceSystemConnectionObject]:
    geo_reference_system = ReferenceSystem(type="GeographicCRS", id="http://www.opengis.net/def/crs/EPSG/0/4326")
    geo_referencing = ReferenceSystemConnectionObject(system=geo_reference_system, coordinates=["y", "x"])

    temporal_reference_system = ReferenceSystem(type="TemporalRS", calendar="Gregorian")
    temporal_referencing = ReferenceSystemConnectionObject(system=temporal_reference_system, coordinates=["t"])

    return [geo_referencing, temporal_referencing]
