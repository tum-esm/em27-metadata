from typing import Any, TypeVar, List
import datetime
import pydantic
import em27_metadata

TimeseriesItem = TypeVar(
    "TimeseriesItem",
    em27_metadata.types.SensorTypes.Location,
    em27_metadata.types.SensorTypes.DifferentUTCOffset,
    em27_metadata.types.SensorTypes.DifferentPressureDataSource,
    em27_metadata.types.SensorTypes.DifferentCalibrationFactors,
)


class EM27MetadataInterface:
    def __init__(
        self,
        locations: List[em27_metadata.types.LocationMetadata],
        sensors: List[em27_metadata.types.SensorMetadata],
        campaigns: List[em27_metadata.types.CampaignMetadata] = [],
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

        self.location_ids = [s.location_id for s in self.locations]
        self.sensor_ids = [s.sensor_id for s in self.sensors]
        self.campaign_ids = [s.campaign_id for s in self.campaigns]

        _test_data_integrity(self.locations, self.sensors, self.campaigns)

    def get(
        self,
        sensor_id: str,
        from_datetime: datetime.datetime,
        to_datetime: datetime.datetime,
    ) -> List[em27_metadata.types.SensorDataContext]:
        """For a given `sensor_id` and `date`, return the list of metadata contexts.
        
        Each "context" is a time period where all metadata properties are constant.
        For example, when requesting a full 24 hour day, and the location changed
        at noon, but all other properties stayed the same, the returned list will
        contain two items: One context until noon, and one context after noon.

        With good organization of the metadata (no frequent switches of utc_offset,
        pressure sources, etc.) the returned list should only contain one or two
        items per day.
        
        Args:
            sensor_id:      The sensor ID.
            from_datetime:  The start of the requested time period.
            to_datetime:    The end of the requested time period.
        
        Returns:  A list of `SensorDataContext` objects.

        Raises:
            ValueError:      If the `sensor_id` is unknown or the `from_datetime` is
                             greater than the given `to_datetime`.
            AssertionError:  If there is a bug in the library.
        """

        # Why is this function so complex? Because every item in the time
        # series can have a different start and end timestamp. And most of
        # code is about determining these constant sections correctly.

        # get the sensor
        if sensor_id not in self.sensor_ids:
            raise ValueError(f'No location data for sensor_id "{sensor_id}"')
        sensor = next(filter(lambda s: s.sensor_id == sensor_id, self.sensors))

        # check if date is valid
        if from_datetime > to_datetime:
            raise ValueError(
                f"from_datetime ({from_datetime}) > to_datetime ({to_datetime})"
            )

        def parse_ts_data(ds: List[TimeseriesItem]) -> List[TimeseriesItem]:
            out: List[TimeseriesItem] = []
            for d in ds:
                if (d.to_datetime
                    <= from_datetime) or (d.from_datetime >= to_datetime):
                    continue

                cropped_d = d.model_copy()
                if cropped_d.from_datetime < from_datetime:
                    cropped_d.from_datetime = from_datetime
                if cropped_d.to_datetime > to_datetime:
                    cropped_d.to_datetime = to_datetime
                out.append(cropped_d)
            return out

        def fill_ts_data_gaps_with_default(
            ds: List[TimeseriesItem], default_item: TimeseriesItem
        ) -> List[TimeseriesItem]:
            out: List[TimeseriesItem] = []

            if len(ds) == 0:
                new_element = default_item.model_copy()
                new_element.from_datetime = from_datetime
                new_element.to_datetime = to_datetime
                out.append(new_element)
            else:
                # if first element starts after requested time period
                if ds[0].from_datetime > from_datetime:
                    new_first_element = default_item.model_copy()
                    new_first_element.from_datetime = from_datetime
                    new_first_element.to_datetime = ds[
                        0].from_datetime - datetime.timedelta(seconds=1)
                    out.append(new_first_element)

                # iterate over all elements and add default elements in between
                # if there is a time gap between two elements
                for i in range(len(ds) - 1):
                    out.append(ds[i])
                    if ds[i].to_datetime < ds[
                        i + 1].from_datetime - datetime.timedelta(seconds=1):
                        new_element = default_item.model_copy()
                        new_element.from_datetime = ds[
                            i].to_datetime + datetime.timedelta(seconds=1)
                        new_element.to_datetime = ds[
                            i +
                            1].from_datetime - datetime.timedelta(seconds=1)
                        out.append(new_element)

                # append last element
                out.append(ds[-1])

                # if last element ends before requested time period
                if ds[-1].to_datetime < to_datetime:
                    new_last_element = default_item.model_copy()
                    new_last_element.from_datetime = ds[
                        -1].to_datetime + datetime.timedelta(seconds=1)
                    new_last_element.to_datetime = to_datetime
                    out.append(new_last_element)

            assert len(out) > 0, "This is a bug in the library"
            for _e1, _e2 in zip(out[:-1], out[1 :]):
                assert (
                    _e1.to_datetime + datetime.timedelta(seconds=1)
                ) == _e2.from_datetime, "This is a bug in the library"

            return out

        # get all locations matching the time period
        sensor_locations = parse_ts_data(sensor.locations)

        # these will be used to fill in time gaps; the values
        # do not matter since they will be overwritten anyway
        default_time_values: Any = {
            "from_datetime": "2000-01-01T00:00:00+00:00",
            "to_datetime": "2000-01-01T00:00:00+00:00",
        }

        # get all properties matching the time period
        # fill data gaps with default values
        utc_offsets = fill_ts_data_gaps_with_default(
            parse_ts_data(sensor.different_utc_offsets),
            em27_metadata.types.SensorTypes.DifferentUTCOffset(
                **default_time_values
            ),
        )

        # get all pressure data sources matching the time period
        # fill data gaps with default values
        pressure_data_sources = fill_ts_data_gaps_with_default(
            parse_ts_data(sensor.different_pressure_data_sources),
            em27_metadata.types.SensorTypes.DifferentPressureDataSource(
                **default_time_values, source=sensor.sensor_id
            ),
        )

        # get all pressure calibration factors matching the time period
        # fill data gaps with default values
        calibration_factors = fill_ts_data_gaps_with_default(
            parse_ts_data(sensor.different_calibration_factors),
            em27_metadata.types.SensorTypes.DifferentCalibrationFactors(
                **default_time_values
            ),
        )

        # now we can assume that we have continuous `utc_offsets`, `pressure_data_sources`,
        # `pressure_calibration_factors` and `output_calibration_factors` time series for
        # the requested time period. Any gaps in the time series have been filled with
        # default values.
        #
        # We also know that the time series are sorted by datetime and that there are no
        # overlaps between the time series. So we are going to iterate over each location
        # and first find the utc_offsets in that period, if only one, we can join it, if two
        # we split the context into to. The we do this joining/splitting for the other time
        # series properties as well.

        breakpoints: List[datetime.datetime] = list(
            sorted(
                set([
                    *[sl.from_datetime for sl in sensor_locations],
                    *[sl.to_datetime for sl in sensor_locations],
                    *[uo.from_datetime for uo in utc_offsets],
                    *[uo.to_datetime for uo in utc_offsets],
                    *[pds.from_datetime for pds in pressure_data_sources],
                    *[pds.to_datetime for pds in pressure_data_sources],
                    *[cf.from_datetime for cf in calibration_factors],
                    *[cf.to_datetime for cf in calibration_factors],
                ])
            )
        )
        sensor_data_contexts: List[em27_metadata.types.SensorDataContext] = []

        for segment_from_datetime, segment_to_datetime in zip(
            breakpoints[:-1], breakpoints[1 :]
        ):

            def _get_segment_property(
                property_list: List[TimeseriesItem]
            ) -> TimeseriesItem:
                """raises IndexError if there is no property for the segment"""
                candidates = list(
                    filter(
                        lambda p: ((
                            p.from_datetime <= segment_from_datetime <= p.
                            to_datetime
                        ) and (
                            p.from_datetime <= segment_to_datetime <= p.
                            to_datetime
                        )),
                        property_list,
                    )
                )
                assert len(candidates) <= 1, "This is a bug in the library"
                return candidates[0]

            try:
                sl = _get_segment_property(sensor_locations)
                uo = _get_segment_property(utc_offsets)
                pds = _get_segment_property(pressure_data_sources)
                cf = _get_segment_property(calibration_factors)
            except IndexError:
                continue

            try:
                location = next(
                    filter(
                        lambda l: l.location_id == sl.location_id,
                        self.locations
                    )
                )
            except StopIteration:
                raise AssertionError("This is a bug in the library")

            sensor_data_contexts.append(
                em27_metadata.types.SensorDataContext(
                    sensor_id=sensor.sensor_id,
                    serial_number=sensor.serial_number,
                    from_datetime=segment_from_datetime,
                    to_datetime=segment_to_datetime,
                    location=location,
                    utc_offset=uo.utc_offset,
                    pressure_data_source=pds.source,
                    calibration_factors=cf,
                    multiple_ctx_on_this_date=False,
                )
            )

        if len(sensor_data_contexts) > 1:
            for ctx in sensor_data_contexts:
                ctx.multiple_ctx_on_this_date = True

        return sensor_data_contexts


class _DatetimeSeriesItem(pydantic.BaseModel):
    from_datetime: datetime.datetime
    to_datetime: datetime.datetime


def _test_data_integrity(
    locations: List[em27_metadata.types.LocationMetadata],
    sensors: List[em27_metadata.types.SensorMetadata],
    campaigns: List[em27_metadata.types.CampaignMetadata],
) -> None:
    """This function tests the integrity of the metadata.
    
    See the `EM27MetadataInterface` constructor for details."""

    location_ids = [s.location_id for s in locations]
    sensor_ids = [s.sensor_id for s in sensors]
    campaign_ids = [s.campaign_id for s in campaigns]

    # unique ids
    assert len(set(location_ids)
              ) == len(location_ids), "location ids are not unique"
    assert len(set(sensor_ids)) == len(sensor_ids), "sensor ids are not unique"
    assert len(set(campaign_ids)
              ) == len(campaign_ids), "campaign ids are not unique"

    # reference existence in sensors.json
    for s1 in sensors:
        for l1 in s1.locations:
            assert l1.location_id in location_ids, f"unknown location id {l1.location_id}"

    # reference existence in campaigns.json
    for c1 in campaigns:
        for _sid in c1.sensor_ids:
            assert _sid in sensor_ids, f"unknown sensor id {_sid}"
        for _lid in c1.location_ids:
            assert _lid in location_ids, f"unknown location id {_lid}"

    # integrity of time series in sensors.json
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
            for _item in timeseries:
                assert (
                    _item.from_datetime < _item.to_datetime
                ), f"from_datetime ({_item.from_datetime}) has to less equal to_datetime ({_item.to_datetime})"

            for _item_1, _item_2 in zip(timeseries[:-1], timeseries[1 :]):
                assert (
                    _item_1.to_datetime < _item_2.from_datetime
                ), f"time periods are overlapping or not sorted: {_item_1.model_dump()}, {_item_2.model_dump()}"
