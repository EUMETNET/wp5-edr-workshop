from __future__ import annotations

import logging
from typing import Annotated

from covjson_pydantic.coverage import Coverage
from covjson_pydantic.coverage import CoverageCollection
from covjson_pydantic.domain import Axes
from covjson_pydantic.domain import Domain
from covjson_pydantic.domain import DomainType
from covjson_pydantic.domain import ValuesAxis
from covjson_pydantic.ndarray import NdArrayFloat
from covjson_pydantic.parameter import Parameter
from edr_pydantic.parameter import EdrBaseModel
from fastapi import APIRouter
from fastapi import Path
from fastapi import Query
from geojson_pydantic import FeatureCollection
from pydantic import AwareDatetime
from starlette.responses import JSONResponse

from api.util import get_covjson_parameter_from_variable
from api.util import get_reference_system
from data.data import get_data
from data.data import get_station
from data.data import get_variables_for_station


router = APIRouter(prefix="/collections/observations")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class CoverageJsonResponse(JSONResponse):
    media_type = "application/prs.coverage+json"


class GeoJsonResponse(JSONResponse):
    media_type = "application/geo+json"


class EDRFeatureCollection(EdrBaseModel, FeatureCollection):
    parameters: dict[str, Parameter]


def get_coverage_for_station(station, parameters) -> Coverage:
    # See if we have any data in this time interval by testing the first parameter
    # TODO: Making assumption here the time interval is the same for all parameters
    data = get_data(station.id, list(parameters)[0])
    t_axis_values = [t for t, v in data]
    # Get parameter data
    ranges = {}
    for p in parameters:
        values = []
        for time, value in get_data(station.id, p):
            values.append(value)

        ranges[p] = NdArrayFloat(
            axisNames=["t", "y", "x"],
            shape=[len(values), 1, 1],
            values=values,
        )

    # Add station code
    station_code = {"eumetnet:locationId": station.wsi}

    domain = Domain(
        domainType=DomainType.point_series,
        axes=Axes(
            x=ValuesAxis[float](values=[station.longitude]),
            y=ValuesAxis[float](values=[station.latitude]),
            t=ValuesAxis[AwareDatetime](values=t_axis_values),
        ),
    )

    return Coverage(domain=domain, ranges=ranges, **station_code)


@router.get(
    "/locations",
    tags=["Collection data queries"],
    response_model=EDRFeatureCollection,
    response_model_exclude_none=True,
    response_class=GeoJsonResponse,
)
async def get_locations(
    bbox: Annotated[str | None, Query(example="5.0,52.0,6.0,52.1")] = None,
    # datetime: Annotated[str | None, Query(example="2024-02-22T01:00:00Z/2024-02-22T02:00:00Z")] = None,
    parameter_name: Annotated[
        str | None,
        Query(
            alias="parameter-name",
            description="Comma seperated list of parameter names. "
            "Return only locations that have one of these parameter.",
            example="ff, dd",
        ),
    ] = None,
) -> EDRFeatureCollection:
    pass


@router.get(
    "/locations/{location_id}",
    tags=["Collection data queries"],
    response_model=CoverageCollection,
    response_model_exclude_none=True,
    response_class=CoverageJsonResponse,
)
async def get_data_location_id(
    location_id: Annotated[str, Path(example="0-20000-0-06260")],
    parameter_name: Annotated[
        str | None,
        Query(alias="parameter-name", description="Comma seperated list of parameter names.", example="ff, dd"),
    ] = None,
    datetime: Annotated[str | None, Query(example="2024-02-22T01:00:00Z/2024-02-22T02:00:00Z")] = None,
) -> CoverageCollection:
    # Location query parameter
    station = get_station(location_id)

    # Parameter_name query parameter
    parameters: dict[str, Parameter] = {
        var.id: get_covjson_parameter_from_variable(var) for var in get_variables_for_station(location_id)
    }

    coverage = get_coverage_for_station(station, parameters)
    return CoverageCollection(coverages=[coverage], parameters=parameters, referencing=get_reference_system())


@router.get(
    "/area",
    tags=["Collection data queries"],
    response_model=CoverageCollection,
    response_model_exclude_none=True,
    response_class=CoverageJsonResponse,
)
async def get_data_area(
    coords: Annotated[str, Query(example="POLYGON((5.0 52.0, 6.0 52.0,6.0 52.1,5.0 52.1, 5.0 52.0))")],
    parameter_name: Annotated[
        str | None,
        Query(alias="parameter-name", description="Comma seperated list of parameter names.", example="ff, dd"),
    ] = None,
    datetime: Annotated[str | None, Query(example="2024-02-22T01:00:00Z/2024-02-22T02:00:00Z")] = None,
) -> CoverageCollection:
    pass
