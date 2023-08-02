import re
from typing import Any, Optional
import pendulum
import pydantic


class TimeSeriesElement(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    from_datetime: pendulum.DateTime
    to_datetime: pendulum.DateTime

    @pydantic.field_validator("from_datetime", "to_datetime", mode="before")
    def name_must_contain_space(cls, v: str) -> pendulum.DateTime:
        assert isinstance(v, str), "must be a string"
        assert TimeSeriesElement.matches_datetime_regex(
            v
        ), "must match the pattern YYYY-MM-DDTHH:MM:SS+HH:MM"
        new_v: Any = pendulum.parser.parse(v, strict=True)
        assert isinstance(new_v, pendulum.DateTime), "must be a datetime"
        return new_v

    @staticmethod
    def matches_datetime_regex(s: str) -> bool:
        datetime_regex = r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})([\+\-])(\d{2}):(\d{2})$"
        return re.match(datetime_regex, s) is not None


class SensorTypes:
    class DifferentUTCOffset(TimeSeriesElement):
        utc_offset: float = pydantic.Field(0, gt=-12, lt=12)

    class DifferentPressureDataSource(TimeSeriesElement):
        source: str = pydantic.Field(..., min_length=1)

    class DifferentPressureCalibrationFactor(TimeSeriesElement):
        factor: float = pydantic.Field(
            1,
            description=(
                "Calibration factor that should be applied multiplicatively: "
                + "expected true value = measured value * factor"
            ),
        )

    class DifferentOutputCalibrationFactor(TimeSeriesElement):
        """These can be either single values to be applied by
        multiplication/division or a list of values for example
        for one airmass-independent and one airmass-dependent
        factor (see Ohyama 2021)."""

        factors_xco2: list[float] = pydantic.Field([1], description="Calibration factors for XCO2.")
        factors_xch4: list[float] = pydantic.Field([1], description="Calibration factors for XCH4.")
        factors_xco: list[float] = pydantic.Field([1], description="Calibration factors for XCO.")
        calibration_scheme: Optional[str] = pydantic.Field(
            None,
            description=(
                'Used calibration scheme - for example "Ohyama 2021".'
                + " This can be an arbitrary string or `null`."
            ),
        )

    class Location(TimeSeriesElement):
        location_id: str = pydantic.Field(
            ...,
            min_length=1,
            description="Location ID referring to a location named in `locations.json`",
        )


class LocationMetadata(pydantic.BaseModel):
    location_id: str = pydantic.Field(
        ...,
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_-]+$",
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
        pattern="^[a-zA-Z0-9_-]+$",
        description="Your internal sensor ID identifying a specific EM27/SUN (system).",
    )
    serial_number: int = pydantic.Field(
        ...,
        ge=1,
        description="Serial number of the EM27/SUN",
    )
    locations: list[SensorTypes.Location] = pydantic.Field(..., min_length=0)

    different_utc_offsets: list[SensorTypes.DifferentUTCOffset] = pydantic.Field(
        [],
        min_length=0,
        description=(
            "List of UTC offsets in which the sensor has recorded "
            + "data. Only required if the UTC offset is non zero."
        ),
    )
    different_pressure_data_sources: list[SensorTypes.DifferentPressureDataSource] = pydantic.Field(
        [],
        min_length=0,
        description=(
            "List of pressure data sources. Only required if the data"
            + " source is the stations built-in pressure sensor."
        ),
    )
    different_pressure_calibration_factors: list[
        SensorTypes.DifferentPressureCalibrationFactor
    ] = pydantic.Field(
        [],
        min_length=0,
        description=(
            "List of pressure calibration factors. Only required "
            + "if the pressure calibration factor is not 1.0."
        ),
    )

    different_output_calibration_factors: list[
        SensorTypes.DifferentOutputCalibrationFactor
    ] = pydantic.Field(
        [],
        min_length=0,
        description="List of output calibration factors.",
    )


class CampaignMetadata(TimeSeriesElement):
    campaign_id: str = pydantic.Field(
        ...,
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_-]+$",
    )
    sensor_ids: list[str]
    location_ids: list[str]


class SensorDataContext(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    sensor_id: str
    serial_number: int
    from_datetime: pendulum.DateTime
    to_datetime: pendulum.DateTime

    location: LocationMetadata
    utc_offset: float
    pressure_data_source: str
    pressure_calibration_factor: float

    output_calibration_factors_xco2: list[float]
    output_calibration_factors_xch4: list[float]
    output_calibration_factors_xco: list[float]
    output_calibration_scheme: Optional[str]
