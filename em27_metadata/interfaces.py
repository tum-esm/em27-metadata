from typing import List
import datetime
import pydantic
import em27_metadata


class EM27MetadataInterface:
    def __init__(
        self,
        locations: em27_metadata.types.LocationMetadataList,
        sensors: em27_metadata.types.SensorMetadataList,
        campaigns: em27_metadata.types.CampaignMetadataList = [],
    ):
        """Create a new EM27MetadataInterface object.

        During the instantiation, the integrity of the metadata is checked by
        running the following tests:

            * Location IDs are unique
            * Sensor IDs are unique
            * Campaign IDs are unique
            * All location IDs referenced in sensors.json exist
            * All sensor IDs referenced in campaigns.json exist
            * All location IDs referenced in campaigns.json exist
            * All time series elements in sensors.json have from_datetime < to_datetime
            * The time series in sensors.json are sorted
            * The time series in sensors.json have no overlaps
        
        Args:
            locations:  A list of `LocationMetadata` objects.
            sensors:    A list of `SensorMetadata` objects.
            campaigns:  A list of `CampaignMetadata` objects.
        
        Returns:  An metadata object containing all the metadata that can now be queried
                  locally using `metadata.get`.
        
        Raises:
            pydantic.ValidationError:  If the metadata integrity checks fail.
        """

        self.locations = locations
        self.sensors = sensors
        self.campaigns = campaigns
        _test_data_integrity(self.locations, self.sensors, self.campaigns)

    def get(
        self,
        sensor_id: str,
        from_datetime: datetime.datetime,
        to_datetime: datetime.datetime,
    ) -> List[em27_metadata.types.SensorDataContext]:
        """For a given `sensor_id`, return the list of metadata contexts between
        `from_datetime` and `to_datetime`.
        
        Each "context" is a time period where the setup and the calibration factors
        are constant. For example, when requesting a full 24 hour day, and the setup
        changed at noon, but the calibration factors stayed the same, the returned list
        willccontain two items: One context until noon, and one context after noon.
        
        Args:
            sensor_id:      The sensor ID.
            from_datetime:  The start of the requested time period.
            to_datetime:    The end of the requested time period.
        
        Returns:  A list of `SensorDataContext` objects.

        Raises:
            ValueError:      If the `sensor_id` is unknown or the `from_datetime` is
                             greater than the given `to_datetime`."""

        try:
            sensor = next(
                filter(lambda s: s.sensor_id == sensor_id, self.sensors)
            )
        except StopIteration:
            raise ValueError(f"Unknown sensor_id {sensor_id}")

        if from_datetime > to_datetime:
            raise ValueError(
                f"from_datetime ({from_datetime}) > to_datetime ({to_datetime})"
            )

        breakpoints: list[datetime.datetime] = sorted([
            dt for dt in set([
                from_datetime,
                *[_l.from_datetime for _l in sensor.locations],
                *[_l.to_datetime for _l in sensor.locations],
                *[_c.from_datetime for _c in sensor.calibration_factors],
                *[_c.to_datetime for _c in sensor.calibration_factors],
                to_datetime,
            ]) if from_datetime <= dt <= to_datetime
        ])

        sensor_data_contexts: List[em27_metadata.types.SensorDataContext] = []
        for from_dt, to_dt in zip(breakpoints[:-1], breakpoints[1 :]):
            try:
                setup = next(
                    filter(
                        lambda s: s.from_datetime <= from_dt <= s.to_datetime,
                        sensor.setups,
                    )
                ).value
                location = next(
                    filter(
                        lambda l: l.location_id == setup.location_id,
                        self.locations,
                    )
                )
            except StopIteration:
                continue
            try:
                calibration_factor = next(
                    filter(
                        lambda c: c.from_datetime <= from_dt <= c.to_datetime,
                        sensor.calibration_factors,
                    )
                )
            except StopIteration:
                # just use the default with all ones
                calibration_factor = em27_metadata.types.CalibrationFactors()

            sensor_data_contexts.append(
                em27_metadata.types.SensorDataContext(
                    sensor_id=sensor.sensor_id,
                    serial_number=sensor.serial_number,
                    from_datetime=from_dt,
                    to_datetime=to_dt,
                    location=location,
                    utc_offset=setup.utc_offset,
                    pressure_data_source=setup.pressure_data_source,
                    calibration_factors=calibration_factor,
                )
            )

        return sensor_data_contexts


class _DatetimeSeriesItem(pydantic.BaseModel):
    from_datetime: datetime.datetime
    to_datetime: datetime.datetime


def _test_data_integrity(
    locations: em27_metadata.types.LocationMetadataList,
    sensors: em27_metadata.types.SensorMetadataList,
    campaigns: em27_metadata.types.CampaignMetadataList,
) -> None:
    """This function tests the integrity of the metadata.
    
    See the `EM27MetadataInterface` constructor for details."""

    # reference existence in sensors.json
    for s1 in sensors.root:
        for l1 in s1.setups:
            assert l1.value.location_id in locations.location_ids, f"unknown location id {l1.location_id}"

    # reference existence in campaigns.json
    for c1 in campaigns.root:
        for _sid in c1.sensor_ids:
            assert _sid in sensors.sensor_ids, f"unknown sensor id {_sid}"
        for _lid in c1.location_ids:
            assert _lid in locations.location_ids, f"unknown location id {_lid}"

    # integrity of time series in sensors.json
    # TODO: move that to root model validators
    for s3 in sensors:
        for timeseries in [
            [_DatetimeSeriesItem(**l2.model_dump()) for l2 in s3.locations],
            [
                _DatetimeSeriesItem(**l2.model_dump())
                for l2 in s3.different_utc_offsets
            ],
            [
                _DatetimeSeriesItem(**l2.model_dump())
                for l2 in s3.different_pressure_data_sources
            ],
            [
                _DatetimeSeriesItem(**l2.model_dump())
                for l2 in s3.different_calibration_factors
            ],
        ]:
            for _item_1, _item_2 in zip(timeseries[:-1], timeseries[1 :]):
                assert (
                    _item_1.to_datetime < _item_2.from_datetime
                ), f"time periods are overlapping or not sorted: {_item_1.model_dump()}, {_item_2.model_dump()}"
