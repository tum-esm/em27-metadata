import re
import pendulum
import pydantic


class TimeSeriesElement(pydantic.BaseModel):
    from_datetime: pendulum.DateTime
    to_datetime: pendulum.DateTime

    @pydantic.validator("from_datetime", "to_datetime", pre=True)
    def name_must_contain_space(cls, v: str):
        assert isinstance(v, str), "must be a string"
        assert TimeSeriesElement.matches_datetime_regex(
            v
        ), "must match the pattern YYYY-MM-DDTHH:MM:SS+HH:MM"
        return pendulum.parser.parse(v, strict=True)

    @staticmethod
    def matches_datetime_regex(s: str) -> bool:
        datetime_regex = r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})([\+\-])(\d{2}):(\d{2})$"
        return re.match(datetime_regex, s) is not None


class SensorTypes:
    class DifferentUTCOffset(TimeSeriesElement):
        utc_offset: float = pydantic.Field(..., gt=-12, lt=12)

    class DifferentPressureDataSource(TimeSeriesElement):
        source: str = pydantic.Field(..., min_length=1)

    class DifferentCalibrationFactor(TimeSeriesElement):
        factor: float = pydantic.Field(
            ...,
            description=(
                "Calibration factor that should be applied multiplicatively: "
                + "expected true value = measured value * factor",
            ),
        )

    class Location(TimeSeriesElement):
        location_id: str = pydantic.Field(
            ...,
            min_length=1,
            description="Location ID referring to a location named in `locations.json`",
        )


class CampaignTypes:
    class Station(pydantic.BaseModel):
        sensor_id: str = pydantic.Field(..., min_length=1)
        default_location_id: str = pydantic.Field(..., min_length=1)
        direction: str = pydantic.Field(
            ...,
            min_length=0,
            description=(
                "Direction of the station, e.g. 'north', 'upwind', etc. It "
                + "is not used for any calculations but just listed in the "
                + "merged output files of the retrieval pipeline.",
            ),
        )


class LocationMetadata(pydantic.BaseModel):
    location_id: str = pydantic.Field(
        ...,
        min_length=1,
        max_length=128,
        regex="^[a-zA-Z0-9_-]+$",
        description="Your internal location ID identifying a specific location.",
    )
    details: str = pydantic.Field("", min_length=0)
    lon: float = pydantic.Field(..., ge=-180, le=180)
    lat: float = pydantic.Field(..., ge=-90, le=90)
    alt: float = pydantic.Field(..., ge=-20, le=10000)


class SensorMetadata(pydantic.BaseModel):
    sensor_id: str = pydantic.Field(
        ...,
        min_length=1,
        max_length=128,
        regex="^[a-zA-Z0-9_-]+$",
        description="Your internal sensor ID identifying a specific EM27/SUN (system).",
    )
    serial_number: int = pydantic.Field(
        ...,
        ge=1,
        description="Serial number of the EM27/SUN",
    )
    locations: list[SensorTypes.Location] = pydantic.Field(..., min_items=0)

    different_utc_offsets: list[SensorTypes.DifferentUTCOffset] = pydantic.Field(
        [],
        min_items=0,
        description=(
            "List of UTC offsets in which the sensor has recorded "
            + "data. Only required if the UTC offset is non zero.",
        ),
    )
    different_pressure_data_sources: list[SensorTypes.DifferentPressureDataSource] = pydantic.Field(
        [],
        min_items=0,
        description=(
            "List of pressure data sources. Only required if the data"
            + " source is the stations built-in pressure sensor."
        ),
    )
    different_pressure_calibration_factors: list[
        SensorTypes.DifferentCalibrationFactor
    ] = pydantic.Field(
        [],
        min_items=0,
        description=(
            "List of pressure calibration factors. Only required "
            + "if the pressure calibration factor is not 1.0."
        ),
    )

    # TODO: add different factors for "xco2", "xch4", etc.
    different_output_calibration_factors: list[
        SensorTypes.DifferentCalibrationFactor
    ] = pydantic.Field(
        [],
        min_items=0,
        description="List of output calibration factors.",
    )


class CampaignMetadata(TimeSeriesElement):
    campaign_id: str = (
        pydantic.Field(
            ...,
            min_length=1,
            max_length=128,
            regex="^[a-zA-Z0-9_-]+$",
        ),
    )
    stations: list[CampaignTypes.Station]
    additional_location_ids: list[str]


class SensorDataContext(pydantic.BaseModel):
    sensor_id: str
    serial_number: int
    utc_offset: float
    pressure_data_source: str
    pressure_calibration_factor: float
    output_calibration_factor: float
    date: str
    location: LocationMetadata
