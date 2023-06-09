from pydantic import BaseModel, validator
from tum_esm_utils.validators import validate_float, validate_int, validate_str


class _TimeSeriesElement(BaseModel):
    from_date: str
    to_date: str

    # validators
    _val_date_string = validator(
        "from_date",
        "to_date",
        pre=True,
        allow_reuse=True,
    )(
        validate_str(is_date_string=True),
    )


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
