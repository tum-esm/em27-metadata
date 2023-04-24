from pydantic import BaseModel
from tum_esm_em27_metadata import types
import pendulum


class EM27MetadataInterface:
    def __init__(
        self,
        locations: list[types.LocationMetadata],
        sensors: list[types.SensorMetadata],
        campaigns: list[types.CampaignMetadata],
    ):
        self.locations = locations
        self.sensors = sensors
        self.campaigns = campaigns

        self.location_ids = [s.location_id for s in self.locations]
        self.sensor_ids = [s.sensor_id for s in self.sensors]
        self.campaign_ids = [s.campaign_id for s in self.campaigns]

        _test_data_integrity(self.locations, self.sensors, self.campaigns)

    def get(self, sensor_id: str, date: str) -> types.SensorDataContext:
        """
        For a given `sensor_id` and `date`, return the metadata. Returns
        the `pydantic` type `tum_esm_em27_metadata.types.SensorDataContext`:

        ```python
        from pydantic import BaseModel

        class Location(BaseModel):
            location_id: str
            details: str
            lon: float
            lat: float
            alt: float

        class SensorDataContext(BaseModel):
            sensor_id: str
            serial_number: int
            utc_offset: float
            pressure_data_source: str
            pressure_calibration_factor: float
            date: str
            location: Location
        ```
        """

        # get the sensor
        assert sensor_id in self.sensor_ids, f'No location data for sensor_id "{sensor_id}"'
        sensor = next(filter(lambda s: s.sensor_id == sensor_id, self.sensors))

        # get utc offset
        try:
            utc_offset = next(
                filter(
                    lambda o: o.from_date <= date <= o.to_date,
                    sensor.different_utc_offsets,
                )
            ).utc_offset
        except StopIteration:
            utc_offset = 0

        # get pressure data source
        try:
            pressure_data_source = next(
                filter(
                    lambda o: o.from_date <= date <= o.to_date,
                    sensor.different_pressure_data_sources,
                )
            ).source
        except StopIteration:
            pressure_data_source = sensor_id

        # get pressure calibration factor
        try:
            pressure_calibration_factor = next(
                filter(
                    lambda o: o.from_date <= date <= o.to_date,
                    sensor.different_pressure_calibration_factors,
                )
            ).factor
        except StopIteration:
            pressure_calibration_factor = 1

        # get output calibration factor
        try:
            output_calibration_factor = next(
                filter(
                    lambda o: o.from_date <= date <= o.to_date,
                    sensor.different_output_calibration_factors,
                )
            ).factor
        except StopIteration:
            output_calibration_factor = 1

        # get location at that date
        try:
            location_id = next(
                filter(
                    lambda l: l.from_date <= date <= l.to_date,
                    sensor.locations,
                )
            ).location_id
        except StopIteration:
            raise ValueError(f"no location data for {sensor_id}/{date}")

        try:
            location = next(filter(lambda l: l.location_id == location_id, self.locations))
        except StopIteration:
            raise ValueError(
                f"unknown location id {location_id}, this is a bug "
                + "and should normally be tested at load-time"
            )

        # bundle the context
        return types.SensorDataContext(
            sensor_id=sensor_id,
            serial_number=sensor.serial_number,
            utc_offset=utc_offset,
            pressure_data_source=pressure_data_source,
            pressure_calibration_factor=pressure_calibration_factor,
            output_calibration_factor=output_calibration_factor,
            date=date,
            location=location,
        )


class _DatetimeSeriesItem(BaseModel):
    from_date: str
    to_date: str


def _test_data_integrity(
    locations: list[types.LocationMetadata],
    sensors: list[types.SensorMetadata],
    campaigns: list[types.CampaignMetadata],
) -> None:
    location_ids = [s.location_id for s in locations]
    sensor_ids = [s.sensor_id for s in sensors]
    campaign_ids = [s.campaign_id for s in campaigns]

    # unique ids
    assert len(set(location_ids)) == len(location_ids), "location ids are not unique"
    assert len(set(sensor_ids)) == len(sensor_ids), "sensor ids are not unique"
    assert len(set(campaign_ids)) == len(campaign_ids), "campaign ids are not unique"

    # reference existence in sensors.json
    for s1 in sensors:
        for l1 in s1.locations:
            assert l1.location_id in location_ids, f"unknown location id {l1.location_id}"

    # reference existence in campaigns.json
    for c1 in campaigns:
        for s2 in c1.stations:
            assert (
                s2.default_location_id in location_ids
            ), f"unknown location id {s2.default_location_id}"
            assert s2.sensor_id in sensor_ids, f"unknown sensor id {s2.sensor_id}"

        for lid in c1.additional_location_ids:
            assert lid in location_ids, f"unknown location id {lid}"

    # integrity of time series in sensors.json
    for s3 in sensors:
        for location_timeseries in [
            [_DatetimeSeriesItem(**l2.dict()) for l2 in s3.locations],
            [_DatetimeSeriesItem(**l2.dict()) for l2 in s3.different_utc_offsets],
            [_DatetimeSeriesItem(**l2.dict()) for l2 in s3.different_pressure_data_sources],
            [_DatetimeSeriesItem(**l2.dict()) for l2 in s3.different_pressure_calibration_factors],
            [_DatetimeSeriesItem(**l2.dict()) for l2 in s3.different_output_calibration_factors],
        ]:
            for l3 in location_timeseries:
                assert (
                    l3.from_date <= l3.to_date
                ), f"from_datetime ({l3.from_date}) has to smaller than to_datetime ({l3.to_date})"

            for i in range(len(location_timeseries) - 1):
                l1_, l2_ = location_timeseries[i : i + 2]
                assert (
                    l1_.to_date <= l2_.from_date
                ), f"time periods are overlapping: {l1_.dict()}, {l1_.dict()}"
