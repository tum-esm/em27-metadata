from typing import Any, TypeVar
import pendulum
from pydantic import BaseModel
from tum_esm_em27_metadata import types


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
        """For a given `sensor_id` and `date`, return the metadata.

        The `date` should be given in `YYYYMMDD` format. Returns the type
        `list[tum_esm_em27_metadata.types.SensorDataContext]`. This list
        contains all locations where the sensor has been at between
        `$date 00:00:00 UTC` and `$date 23:59:59 UTC`.

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
            utput_calibration_factor_xco2: float
            utput_calibration_factor_xch4: float
            utput_calibration_factor_xco: float
            from_datetime: pendulum.DateTime
            to_datetime: pendulum.DateTime
            location: Location
        ```

        Why is this so complex? Because every item in the time series
        can have a different start and end timestamp. Every sensor data
        context describes a time period where all of these properties
        have a constant value.

        With good organization of the metadata (no frequent switches
        of utc_offset, pressure sources, etc.) the returned list should
        only contain one or two items when the requested time period is
        24 hours.

        The requested time period is not fixed on a date because some
        teams (e.g. Japan) might record data from 22:00 UTC to 10:00 UTC
        the next day: So the requested time period is 10 hours long, but
        the data is recorded over two days. The retrieval currently does
        not explicitly support this case yet because we don't know, how
        overseas teams organize their data. But with the getter function,
        the changes to the retrieval pipeline should be minimal."""

        # get the sensor
        assert sensor_id in self.sensor_ids, f'No location data for sensor_id "{sensor_id}"'
        sensor = next(filter(lambda s: s.sensor_id == sensor_id, self.sensors))

        # check if date is valid
        assert (
            from_datetime <= to_datetime
        ), f"from_datetime ({from_datetime}) > to_datetime ({to_datetime})"

        T = TypeVar(
            "T",
            types.SensorTypes.Location,
            types.SensorTypes.DifferentUTCOffset,
            types.SensorTypes.DifferentPressureDataSource,
            types.SensorTypes.DifferentPressureCalibrationFactor,
            types.SensorTypes.DifferentOutputCalibrationFactor,
        )

        def parse_ts_data(ds: list[T]) -> list[T]:
            out: list[T] = []
            for d in ds:
                if (d.to_datetime < from_datetime) or (d.from_datetime > to_datetime):
                    continue

                cropped_d = d.copy()
                if cropped_d.from_datetime < from_datetime:
                    cropped_d.from_datetime = from_datetime
                if cropped_d.to_datetime > to_datetime:
                    cropped_d.to_datetime = to_datetime
                out.append(cropped_d)
            return out

        def fill_ts_data_gaps_with_default(ds: list[T], default_item: T) -> list[T]:
            out: list[T] = []

            if len(ds) == 0:
                new_element = default_item.copy()
                new_element.from_datetime = from_datetime
                new_element.to_datetime = to_datetime
                out.append(new_element)
            else:
                # if first element starts after requested time period
                if ds[0].from_datetime > from_datetime:
                    new_first_element = default_item.copy()
                    new_first_element.from_datetime = from_datetime
                    new_first_element.to_datetime = ds[0].from_datetime.subtract(seconds=1)  # type: ignore
                    out.append(new_first_element)

                # iterate over all elements and add default elements in between
                # if there is a time gap between two elements
                for i in range(len(ds) - 1):
                    out.append(ds[i])
                    if ds[i].to_datetime < ds[i + 1].from_datetime.subtract(seconds=1):  # type: ignore
                        new_element = default_item.copy()
                        new_element.from_datetime = ds[i].to_datetime.add(seconds=1)
                        new_element.to_datetime = ds[i + 1].from_datetime.subtract(seconds=1)  # type: ignore
                        out.append(new_element)
                    out.append(ds[i + 1])

                # append last element
                out.append(ds[-1])

                # if last element ends before requested time period
                if ds[-1].to_datetime < to_datetime:
                    new_last_element = default_item.copy()
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
            types.SensorTypes.DifferentUTCOffset(**default_time_values, utc_offset=0.0),
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
            types.SensorTypes.DifferentPressureCalibrationFactor(**default_time_values, factor=1.0),
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

        sensor_data_contexts: list[types.SensorDataContext] = []

        for sl in sensor_locations:
            t1_from = sl.from_datetime
            t1_to = sl.to_datetime

            try:
                location = next(filter(lambda l: l.location_id == sl.location_id, self.locations))
            except StopIteration:
                raise ValueError(
                    f"unknown location id {sl.location_id}, this is a bug "
                    + "and should normally be tested at load-time"
                )

            for uo in utc_offsets:
                if (t1_to < uo.from_datetime) or (uo.to_datetime < t1_from):
                    continue

                t2_from = max(t1_from, uo.from_datetime)
                t2_to = min(t1_to, uo.to_datetime)

                for pds in pressure_data_sources:
                    if (t2_to < pds.from_datetime) or (pds.to_datetime < t2_from):
                        continue

                    t3_from = max(t2_from, pds.from_datetime)
                    t3_to = min(t2_to, pds.to_datetime)

                    for pcf in pressure_calibration_factors:
                        if (t3_to < pcf.from_datetime) or (pcf.to_datetime < t3_from):
                            continue

                        t4_from = max(t3_from, pcf.from_datetime)
                        t4_to = min(t3_to, pcf.to_datetime)

                        for ocf in output_calibration_factors:
                            if (t4_to < ocf.from_datetime) or (ocf.to_datetime < t4_from):
                                continue

                            t5_from = max(t4_from, ocf.from_datetime)
                            t5_to = min(t4_to, ocf.to_datetime)

                            sensor_data_contexts.append(
                                types.SensorDataContext(
                                    sensor_id=sensor.sensor_id,
                                    serial_number=sensor.serial_number,
                                    utc_offset=uo.utc_offset,
                                    pressure_data_source=pds.source,
                                    pressure_calibration_factor=pcf.factor,
                                    output_calibration_factor_xco2=ocf.factor_xco2,
                                    output_calibration_factor_xch4=ocf.factor_xch4,
                                    output_calibration_factor_xco=ocf.factor_xco,
                                    from_datetime=t5_from,
                                    to_datetime=t5_to,
                                    location=location,
                                )
                            )

        return sensor_data_contexts


class _DatetimeSeriesItem(BaseModel):
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
                    l3.from_datetime <= l3.to_datetime
                ), f"from_datetime ({l3.from_datetime}) has to less equal to_datetime ({l3.to_datetime})"

            for i in range(len(location_timeseries) - 1):
                l1_, l2_ = location_timeseries[i : i + 2]
                assert (
                    l1_.to_datetime <= l2_.from_datetime
                ), f"time periods are overlapping or not sorted: {l1_.dict()}, {l1_.dict()}"
