from typing import Any, TypeVar
import pendulum
import pydantic
from tum_esm_em27_metadata import types

T = TypeVar(
    "T",
    types.SensorTypes.Location,
    types.SensorTypes.DifferentUTCOffset,
    types.SensorTypes.DifferentPressureDataSource,
    types.SensorTypes.DifferentPressureCalibrationFactor,
    types.SensorTypes.DifferentOutputCalibrationFactor,
)


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

    def get(
        self,
        sensor_id: str,
        from_datetime: pendulum.DateTime,
        to_datetime: pendulum.DateTime,
    ) -> list[types.SensorDataContext]:
        """For a given `sensor_id` and `date`, return the metadata. The
        returned list contains all locations at which the sensor has been
        at between `$date 00:00:00 UTC` and `$date 23:59:59 UTC`. Each
        item in the list is a `SensorDataContext` object which has
        constant properties for the respective time period (same location,
        UTC offset, pressure data source, calibration factors). I.e. when
        requesting 24 hours and the location changed at noon, but all
        other properties stayed the same, the returned list will contain
        two items: One until noon, and one after noon.

        Why is this so complex? Because every item in the time series
        can have a different start and end timestamp. Every sensor data
        context describes a time period where all of these properties
        have a constant value.

        With good organization of the metadata (no frequent switches
        of utc_offset, pressure sources, etc.) the returned list should
        only contain one or two items per day.

        The requested time period is not fixed on a date because some
        teams (e.g. Japan) might record data from 22:00 UTC to 10:00 UTC
        the next day: So the requested time period is 10 hours long, but
        the data is recorded over two days. The retrieval currently does
        not explicitly support this case yet because we don't know, how
        overseas teams organize their data. But with this getter-function,
        the changes to the retrieval pipeline should be minimal."""

        # get the sensor
        assert sensor_id in self.sensor_ids, f'No location data for sensor_id "{sensor_id}"'
        sensor = next(filter(lambda s: s.sensor_id == sensor_id, self.sensors))

        # check if date is valid
        assert (
            from_datetime <= to_datetime
        ), f"from_datetime ({from_datetime}) > to_datetime ({to_datetime})"

        def parse_ts_data(ds: list[T]) -> list[T]:
            out: list[T] = []
            for d in ds:
                if (d.to_datetime <= from_datetime) or (d.from_datetime >= to_datetime):
                    continue

                cropped_d = d.model_copy()
                if cropped_d.from_datetime < from_datetime:
                    cropped_d.from_datetime = from_datetime
                if cropped_d.to_datetime > to_datetime:
                    cropped_d.to_datetime = to_datetime
                out.append(cropped_d)
            return out

        def fill_ts_data_gaps_with_default(ds: list[T], default_item: T) -> list[T]:
            out: list[T] = []

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
                    new_first_element.to_datetime = ds[0].from_datetime.subtract(seconds=1)  # type: ignore
                    out.append(new_first_element)

                # iterate over all elements and add default elements in between
                # if there is a time gap between two elements
                for i in range(len(ds) - 1):
                    out.append(ds[i])
                    if ds[i].to_datetime < ds[i + 1].from_datetime.subtract(seconds=1):  # type: ignore
                        new_element = default_item.model_copy()
                        new_element.from_datetime = ds[i].to_datetime.add(seconds=1)
                        new_element.to_datetime = ds[i + 1].from_datetime.subtract(seconds=1)  # type: ignore
                        out.append(new_element)

                # append last element
                out.append(ds[-1])

                # if last element ends before requested time period
                if ds[-1].to_datetime < to_datetime:
                    new_last_element = default_item.model_copy()
                    new_last_element.from_datetime = ds[-1].to_datetime.add(seconds=1)
                    new_last_element.to_datetime = to_datetime
                    out.append(new_last_element)

            assert len(out) > 0, "This is a bug in the library"
            for _e1, _e2 in zip(out[:-1], out[1:]):
                assert (
                    _e1.to_datetime.add(seconds=1) == _e2.from_datetime
                ), "This is a bug in the library"

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
            types.SensorTypes.DifferentUTCOffset(**default_time_values),
        )

        # get all pressure data sources matching the time period
        # fill data gaps with default values
        pressure_data_sources = fill_ts_data_gaps_with_default(
            parse_ts_data(sensor.different_pressure_data_sources),
            types.SensorTypes.DifferentPressureDataSource(
                **default_time_values, source=sensor.sensor_id
            ),
        )

        # get all pressure calibration factors matching the time period
        # fill data gaps with default values
        pressure_calibration_factors = fill_ts_data_gaps_with_default(
            parse_ts_data(sensor.different_pressure_calibration_factors),
            types.SensorTypes.DifferentPressureCalibrationFactor(**default_time_values),
        )

        # get all output calibration factors matching the time period
        # fill data gaps with default values
        output_calibration_factors = fill_ts_data_gaps_with_default(
            parse_ts_data(sensor.different_output_calibration_factors),
            types.SensorTypes.DifferentOutputCalibrationFactor(**default_time_values),
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

        breakpoints: list[pendulum.DateTime] = list(
            sorted(
                set(
                    [
                        *[sl.from_datetime for sl in sensor_locations],
                        *[sl.to_datetime for sl in sensor_locations],
                        *[uo.from_datetime for uo in utc_offsets],
                        *[uo.to_datetime for uo in utc_offsets],
                        *[pds.from_datetime for pds in pressure_data_sources],
                        *[pds.to_datetime for pds in pressure_data_sources],
                        *[pcf.from_datetime for pcf in pressure_calibration_factors],
                        *[pcf.to_datetime for pcf in pressure_calibration_factors],
                        *[ocf.from_datetime for ocf in output_calibration_factors],
                        *[ocf.to_datetime for ocf in output_calibration_factors],
                    ]
                )
            )
        )
        sensor_data_contexts: list[types.SensorDataContext] = []

        for segment_from_datetime, segment_to_datetime in zip(breakpoints[:-1], breakpoints[1:]):

            def _get_segment_property(property_list: list[T]) -> T:
                """raises IndexError if there is no property for the segment"""
                candidates = list(
                    filter(
                        lambda p: (
                            (p.from_datetime <= segment_from_datetime <= p.to_datetime)
                            and (p.from_datetime <= segment_to_datetime <= p.to_datetime)
                        ),
                        property_list,
                    )
                )
                assert len(candidates) <= 1, "This is a bug in the library"
                return candidates[0]

            try:
                sl = _get_segment_property(sensor_locations)
                uo = _get_segment_property(utc_offsets)
                pds = _get_segment_property(pressure_data_sources)
                pcf = _get_segment_property(pressure_calibration_factors)
                ocf = _get_segment_property(output_calibration_factors)
            except IndexError:
                continue

            try:
                location = next(filter(lambda l: l.location_id == sl.location_id, self.locations))
            except StopIteration:
                raise AssertionError("This is a bug in the library")

            sensor_data_contexts.append(
                types.SensorDataContext(
                    sensor_id=sensor.sensor_id,
                    serial_number=sensor.serial_number,
                    from_datetime=segment_from_datetime,
                    to_datetime=segment_to_datetime,
                    location=location,
                    utc_offset=uo.utc_offset,
                    pressure_data_source=pds.source,
                    pressure_calibration_factor=pcf.factor,
                    output_calibration_factors_xco2=ocf.factors_xco2,
                    output_calibration_factors_xch4=ocf.factors_xch4,
                    output_calibration_factors_xco=ocf.factors_xco,
                    output_calibration_scheme=ocf.calibration_scheme,
                )
            )

        return sensor_data_contexts


class _DatetimeSeriesItem(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    from_datetime: pendulum.DateTime
    to_datetime: pendulum.DateTime


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
        for _sid in c1.sensor_ids:
            assert _sid in sensor_ids, f"unknown sensor id {_sid}"
        for _lid in c1.location_ids:
            assert _lid in location_ids, f"unknown location id {_lid}"

    # integrity of time series in sensors.json
    for s3 in sensors:
        for timeseries in [
            [_DatetimeSeriesItem(**l2.model_dump()) for l2 in s3.locations],
            [_DatetimeSeriesItem(**l2.model_dump()) for l2 in s3.different_utc_offsets],
            [_DatetimeSeriesItem(**l2.model_dump()) for l2 in s3.different_pressure_data_sources],
            [
                _DatetimeSeriesItem(**l2.model_dump())
                for l2 in s3.different_pressure_calibration_factors
            ],
            [
                _DatetimeSeriesItem(**l2.model_dump())
                for l2 in s3.different_output_calibration_factors
            ],
        ]:
            for _item in timeseries:
                assert (
                    _item.from_datetime < _item.to_datetime
                ), f"from_datetime ({_item.from_datetime}) has to less equal to_datetime ({_item.to_datetime})"

            for _item_1, _item_2 in zip(timeseries[:-1], timeseries[1:]):
                assert (
                    _item_1.to_datetime < _item_2.from_datetime
                ), f"time periods are overlapping or not sorted: {_item_1.model_dump()}, {_item_2.model_dump()}"
