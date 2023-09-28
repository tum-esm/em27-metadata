from __future__ import annotations
from typing import Any, Optional, List
import datetime
import re
import pydantic


class TimeSeriesElement(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    from_datetime: datetime.datetime
    to_datetime: datetime.datetime

    @pydantic.field_validator("from_datetime", "to_datetime", mode="before")
    def name_must_contain_space(cls, v: str) -> datetime.datetime:
        assert isinstance(v, str), "must be a string"
        assert TimeSeriesElement.matches_datetime_regex(
            v
        ), "must match the pattern YYYY-MM-DDTHH:MM:SS+HH:MM"
        return datetime.datetime.fromisoformat(v)

    @staticmethod
    def matches_datetime_regex(s: str) -> bool:
        datetime_regex = r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})([\+\-])(\d{2}):(\d{2})$"
        return re.match(datetime_regex, s) is not None

    @pydantic.field_serializer("from_datetime", "to_datetime")
    def t_serializer(self, dt: datetime.date, _info: Any) -> str:
        return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")


class CalibrationFactorsItem(pydantic.BaseModel):
    factors: List[float] = pydantic.Field(
        [1],
        description=
        "List of calibration factors. The scheme defines how to use them.",
    )
    scheme: Optional[str] = pydantic.Field(
        None,
        description='Used calibration scheme - for example "Ohyama 2021".' +
        " This can be an arbitrary string or `null`.",
    )
    note: Optional[str] = pydantic.Field(
        None,
        description=
        'Optional note, e.g. "actual = factors[0] * measured + factors[1]"',
    )


class CalibrationFactors(pydantic.BaseModel):
    """These can be either single values to be applied by
        multiplication/division or a list of values for example
        for one airmass-independent and one airmass-dependent
        factor (see Ohyama 2021)."""

    pressure: float = pydantic.Field(
        1, description="Pressure calibration factor. real = measured * factor"
    )
    xco2: CalibrationFactorsItem = pydantic.Field(CalibrationFactorsItem())
    xch4: CalibrationFactorsItem = pydantic.Field(CalibrationFactorsItem())
    xco: CalibrationFactorsItem = pydantic.Field(CalibrationFactorsItem())


class SensorTypes:
    class DifferentUTCOffset(TimeSeriesElement):
        utc_offset: float = pydantic.Field(0, gt=-12, lt=12)

    class DifferentPressureDataSource(TimeSeriesElement):
        source: str = pydantic.Field(..., min_length=1)

    class DifferentCalibrationFactors(TimeSeriesElement, CalibrationFactors):
        """The same as `CalibrationFactors` but with a time window."""

    class Location(TimeSeriesElement):
        location_id: str = pydantic.Field(
            ...,
            min_length=1,
            description=
            "Location ID referring to a location named in `locations.json`",
        )


class LocationMetadata(pydantic.BaseModel):
    location_id: str = pydantic.Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description=(
            "Your internal location ID identifying a specific location. " +
            "Allowed values: letters, numbers, dashes, underscores."
        ),
    )
    details: str = pydantic.Field("", min_length=0)
    lon: float = pydantic.Field(..., ge=-180, le=180)
    lat: float = pydantic.Field(..., ge=-90, le=90)
    alt: float = pydantic.Field(..., ge=-20, le=10000)


class LocationMetadataList(pydantic.BaseModel):
    locations: List[LocationMetadata]


class SensorMetadata(pydantic.BaseModel):
    """Metadata for a single sensor.
    
    `sensor_id`, `serial_number` and `locations` are required. The other items
    - `different_utc_offsets`, `different_pressure_data_sources` and 
    `different_calibration_factors` - are only needed of they deviate from the
    default values (no UTC offset, pressure data source is "built-in" on,
    no calibration of pressure or output values)."""

    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    sensor_id: str = pydantic.Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description=(
            "Your internal sensor ID identifying a specific EM27/SUN (system). "
            + "Allowed characters: letters, numbers, dashes, underscores."
        ),
    )
    serial_number: int = pydantic.Field(
        ...,
        ge=1,
        description="Serial number of the EM27/SUN",
    )
    locations: List[SensorTypes.Location] = pydantic.Field(..., min_length=0)
    different_utc_offsets: List[
        SensorTypes.DifferentUTCOffset] = pydantic.Field(
            [],
            min_length=0,
            description=(
                "List of UTC offsets in which the sensor has recorded " +
                "data. Only required if the UTC offset is non zero."
            ),
        )
    different_pressure_data_sources: List[
        SensorTypes.DifferentPressureDataSource] = pydantic.Field(
            [],
            min_length=0,
            description=(
                "List of pressure data sources. Only required if the data" +
                " source is the stations built-in pressure sensor."
            ),
        )
    different_calibration_factors: List[
        SensorTypes.DifferentCalibrationFactors
    ] = pydantic.Field(
        [],
        description=(
            "List of calibration factors to used. Only required if the" +
            "calibration factor is not 1.0. The pressure calibration factor" +
            " is applied before the retrieval, the other factors are applied" +
            " to the results delivered by Proffast/GFIT."
        ),
    )


class SensorMetadataList(pydantic.BaseModel):
    sensors: List[SensorMetadata]


class CampaignMetadata(TimeSeriesElement):
    campaign_id: str = pydantic.Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description=(
            "Your internal sensor ID identifying a specific campaign. " +
            "Allowed values: letters, numbers, dashes, underscores."
        ),
    )
    sensor_ids: List[str]
    location_ids: List[str]


class CampaignMetadataList(pydantic.BaseModel):
    campaigns: List[CampaignMetadata]


class SensorDataContext(pydantic.BaseModel):
    sensor_id: str
    serial_number: int
    from_datetime: datetime.datetime
    to_datetime: datetime.datetime
    location: LocationMetadata

    # set to default values if not specified
    utc_offset: float
    pressure_data_source: str
    calibration_factors: CalibrationFactors

    multiple_ctx_on_this_date: bool

    @pydantic.field_serializer("from_datetime", "to_datetime")
    def t_serializer(self, dt: datetime.date, _info: Any) -> str:
        return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
