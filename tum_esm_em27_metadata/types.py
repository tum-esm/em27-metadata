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

    class DifferentPressureCalibrationFactor(TimeSeriesElement):
        factor: float = pydantic.Field(..., ge=0.1, le=1.9)

    class DifferentOutputCalibrationFactor(TimeSeriesElement):
        factor: float = pydantic.Field(..., ge=0.1, le=1.9)

    class Location(TimeSeriesElement):
        location_id: str


class CampaignTypes:
    class Station(pydantic.BaseModel):
        sensor_id: str = pydantic.Field(..., min_length=1)
        default_location_id: str = pydantic.Field(..., min_length=1)
        direction: str = pydantic.Field(..., min_length=0)


class LocationMetadata(pydantic.BaseModel):
    location_id: str = pydantic.Field(
        ...,
        min_length=1,
        max_length=128,
        regex="^[a-zA-Z0-9_-]+$",
    )
    details: str = pydantic.Field(..., min_length=1)
    lon: float = pydantic.Field(..., ge=-180, le=180)
    lat: float = pydantic.Field(..., ge=-90, le=90)
    alt: float = pydantic.Field(..., ge=-20, le=10000)


class SensorMetadata(pydantic.BaseModel):
    sensor_id: str = (
        pydantic.Field(
            ...,
            min_length=1,
            max_length=128,
            regex="^[a-zA-Z0-9_-]+$",
        ),
    )
    serial_number: int = pydantic.Field(..., ge=1)
    different_utc_offsets: list[SensorTypes.DifferentUTCOffset]
    different_pressure_data_sources: list[SensorTypes.DifferentPressureDataSource]
    different_pressure_calibration_factors: list[SensorTypes.DifferentPressureCalibrationFactor]
    different_output_calibration_factors: list[SensorTypes.DifferentOutputCalibrationFactor]
    locations: list[SensorTypes.Location]


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
