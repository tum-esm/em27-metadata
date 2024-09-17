from __future__ import annotations
from typing import Any, Optional
import datetime
import re
import pydantic


class TimeSeriesElement(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    from_datetime: datetime.datetime
    to_datetime: datetime.datetime

    @pydantic.field_validator("from_datetime", "to_datetime", mode="before")
    def datetime_string_validator(
        cls, v: str | datetime.datetime
    ) -> datetime.datetime:
        if isinstance(v, datetime.datetime):
            return v
        assert isinstance(v, str), "must be a string"
        assert TimeSeriesElement.matches_datetime_regex(
            v
        ), "must match the pattern YYYY-MM-DDTHH:MM:SS+HHMM"
        return datetime.datetime.strptime(v, "%Y-%m-%dT%H:%M:%S%z")

    @staticmethod
    def matches_datetime_regex(v: str) -> bool:
        return re.match(
            r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})([\+\-])(\d{4})$",
            v
        ) is not None

    @pydantic.model_validator(mode="after")
    def model_validator(self) -> TimeSeriesElement:
        assert self.from_datetime < self.to_datetime, "from_datetime must be before to_datetime"
        assert self.from_datetime.second == 0, "from_datetime must be at the beginning of a minute"
        assert self.to_datetime.second == 59, "to_datetime must be at the beginning of a minute"
        return self

    @pydantic.field_serializer("from_datetime", "to_datetime")
    def t_serializer(self, dt: datetime.date, _info: Any) -> str:
        return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")


class Setup(pydantic.BaseModel):
    location_id: str = pydantic.Field(
        ...,
        min_length=1,
        description=
        "Location ID referring to a location named in `locations.json`",
    )
    pressure_data_source: Optional[str] = pydantic.Field(
        None,
        min_length=1,
        description=
        "Pressure data source, if not set, using the pressure of the sensor",
    )
    utc_offset: float = pydantic.Field(
        0,
        gt=-12,
        lt=12,
        description=
        "UTC offset of the location, if not set, using an offset of 0",
    )
    atmospheric_profile_location_id: Optional[str] = pydantic.Field(
        None,
        min_length=1,
        description=
        "Location ID referring to a location named in `locations.json`. This location's coordinates are used for the atmospheric profiles in the retrieval.",
    )


class SetupsListItem(TimeSeriesElement):
    """An element in the `sensor.setups` list"""
    value: Setup


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


class LocationMetadataList(pydantic.RootModel[list[LocationMetadata]]):
    root: list[LocationMetadata]

    @property
    def location_ids(self: LocationMetadataList) -> list[str]:
        return [_l.location_id for _l in self.root]

    @pydantic.model_validator(mode="after")
    def check_id_uniqueness(self: LocationMetadataList) -> LocationMetadataList:
        if len(self.location_ids) > len(set(self.location_ids)):
            raise ValueError("Location IDs should be unique")
        return self


class SensorMetadata(pydantic.BaseModel):
    """Metadata for a single sensor."""

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
    setups: list[SetupsListItem] = pydantic.Field(..., min_length=0)
    calibration_factors: list[Any] = pydantic.Field(
        [],
        deprecated=(
            "This field has been deprecated. Every Research group has their " +
            "own strategy of calibrating their data, hence, we don't want to " +
            "propose any standard with this. Also it calibration is more " +
            "complex than just multiplying a factor to the data."
        ),
        exclude=True
    )

    @pydantic.model_validator(mode="after")
    def check_timeseries_integrity(self: SensorMetadata) -> SensorMetadata:
        for s1, s2 in zip(self.setups[:-1], self.setups[1 :]):
            if s2.from_datetime <= s1.to_datetime:
                raise ValueError(
                    "Setups timeseries are overlapping or unsorted"
                )
        return self


class SensorMetadataList(pydantic.RootModel[list[SensorMetadata]]):
    root: list[SensorMetadata]

    @property
    def sensor_ids(self: SensorMetadataList) -> list[str]:
        return [_l.sensor_id for _l in self.root]

    @pydantic.model_validator(mode="after")
    def check_id_uniqueness(self: SensorMetadataList) -> SensorMetadataList:
        if len(self.sensor_ids) > len(set(self.sensor_ids)):
            raise ValueError("Sensor IDs should be unique")
        return self


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
    sensor_ids: list[str]
    location_ids: list[str]


class CampaignMetadataList(pydantic.RootModel[list[CampaignMetadata]]):
    root: list[CampaignMetadata] = []

    @property
    def campaign_ids(self: CampaignMetadataList) -> list[str]:
        return [_l.campaign_id for _l in self.root]

    @pydantic.model_validator(mode="after")
    def check_id_uniqueness(self: CampaignMetadataList) -> CampaignMetadataList:
        if len(self.campaign_ids) > len(set(self.campaign_ids)):
            raise ValueError("Campaign IDs should be unique")
        return self


class SensorDataContext(pydantic.BaseModel):
    sensor_id: str
    serial_number: int
    from_datetime: datetime.datetime
    to_datetime: datetime.datetime
    location: LocationMetadata

    # set to default values if not specified
    utc_offset: float
    pressure_data_source: str
    calibration_factors: Any = pydantic.Field(
        None,
        deprecated=(
            "This field has been deprecated. Every Research group has their " +
            "own strategy of calibrating their data, hence, we don't want to " +
            "propose any standard with this. Also it calibration is more " +
            "complex than just multiplying a factor to the data."
        ),
        exclude=True
    )
    atmospheric_profile_location: LocationMetadata

    @pydantic.field_serializer("from_datetime", "to_datetime")
    def t_serializer(self, dt: datetime.date, _info: Any) -> str:
        return dt.strftime("%Y-%m-%dT%H:%M:%S%z")
