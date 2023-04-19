from datetime import datetime, timedelta
import json
from typing import Any, Callable, Optional, Union
import tum_esm_utils
from tum_esm_em27_metadata import types


class EM27MetadataInterface:
    def __init__(
        self,
        locations: list[types.Location],
        sensors: list[types.Sensor],
        campaigns: list[types.Campaign],
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
        sensor = list(filter(lambda s: s.sensor_id == sensor_id, self.sensors))[0]

        # get utc offset
        utc_offset_matches = list(
            filter(
                lambda o: o.from_date <= date <= o.to_date,
                sensor.utc_offsets,
            )
        )
        assert len(utc_offset_matches) == 1, f"no utc offset data for {sensor_id}/{date}"
        utc_offset = utc_offset_matches[0].utc_offset

        # get pressure data source
        pressure_data_source_matches = list(
            filter(
                lambda o: o.from_date <= date <= o.to_date,
                sensor.different_pressure_data_source,
            )
        )
        pressure_data_source = (
            sensor_id
            if len(pressure_data_source_matches) == 0
            else pressure_data_source_matches[0].source
        )

        # get pressure calibration factor
        pressure_calibration_factor_matches = list(
            filter(
                lambda o: o.from_date <= date <= o.to_date,
                sensor.pressure_calibration_factors,
            )
        )
        assert (
            len(pressure_calibration_factor_matches) == 1
        ), f"no pressure calibration data for {sensor_id}/{date}"
        pressure_calibration_factor = pressure_calibration_factor_matches[0].factor

        # get location at that date
        location_matches = list(
            filter(
                lambda l: l.from_date <= date <= l.to_date,
                sensor.locations,
            )
        )
        assert len(location_matches) == 1, f"no location data for {sensor_id}/{date}"
        location_id = location_matches[0].location_id
        location = list(filter(lambda l: l.location_id == location_id, self.locations))[0]

        # bundle the context
        return types.SensorDataContext(
            sensor_id=sensor_id,
            serial_number=sensor.serial_number,
            utc_offset=utc_offset,
            pressure_data_source=pressure_data_source,
            pressure_calibration_factor=pressure_calibration_factor,
            date=date,
            location=location,
        )


def load_from_github(
    github_repository: str,
    access_token: Optional[str] = None,
) -> EM27MetadataInterface:
    """loads an EM27MetadataInterface from GitHub"""

    _req: Callable[[str], list[Any]] = lambda t: json.loads(
        tum_esm_utils.github.request_github_file(
            github_repository=github_repository,
            filepath=f"data/{t}.json",
            access_token=access_token,
        )
    )

    return EM27MetadataInterface(
        locations=[types.Location(**l) for l in _req("locations")],
        sensors=[types.Sensor(**l) for l in _req("sensors")],
        campaigns=[types.Campaign(**l) for l in _req("campaigns")],
    )


ALLOWED_EXTRA_PRESSURE_DATA_SOURCES = ["LMU-MIM01-height-adjusted"]


def _test_data_integrity(
    locations: list[types.Location],
    sensors: list[types.Sensor],
    campaigns: list[types.Campaign],
) -> None:
    location_ids = [s.location_id for s in locations]
    sensor_ids = [s.sensor_id for s in sensors]
    campaign_ids = [s.campaign_id for s in campaigns]

    # unique ids
    assert len(set(location_ids)) == len(location_ids), "location ids are not unique"
    assert len(set(sensor_ids)) == len(sensor_ids), "sensor ids are not unique"
    assert len(set(campaign_ids)) == len(campaign_ids), "campaign ids are not unique"

    # reference existence in sensors.json
    for s in sensors:
        for l in s.locations:
            assert l.location_id in location_ids, f"unknown location id {l.location_id}"
        for p in s.different_pressure_data_source:
            assert p.source in (
                sensor_ids + ALLOWED_EXTRA_PRESSURE_DATA_SOURCES
            ), f"unknown pressure data source {p.source}"

    # reference existence in campaigns.json
    for c in campaigns:
        for s2 in c.stations:
            assert (
                s2.default_location_id in location_ids
            ), f"unknown location id {s2.default_location_id}"
            assert s2.sensor_id in sensor_ids, f"unknown sensor id {s2.sensor_id}"

    # integrity of time series in sensors.json
    for s in sensors:

        # TEST TIME SERIES INTEGRITY OF "utc_offsets",
        # "pressure_calibration_factors", and "locations"
        xss: list[
            Union[
                list[types.SensorUTCOffset],
                list[types.SensorPressureCalibrationFactor],
                list[types.SensorLocation],
            ]
        ] = [s.utc_offsets, s.pressure_calibration_factors, s.locations]
        for xs in xss:
            for x in xs:
                assert x.from_date <= x.to_date, (
                    "from_date has to smaller than to_date " + f"({x.from_date} > {x.to_date})"
                )
            for i in range(len(xs) - 1):
                x1, x2 = xs[i : i + 2]
                expected_x2_from_date = (
                    datetime.strptime(x1.to_date, "%Y%m%d") + timedelta(days=1)
                ).strftime("%Y%m%d")
                assert not (
                    expected_x2_from_date > x2.from_date
                ), f"time periods are overlapping: {x1.dict()}, {x1.dict()}"
                assert not (
                    expected_x2_from_date < x2.from_date
                ), f"time periods have gaps: {x1.dict()}, {x1.dict()}"

        # TEST TIME SERIES INTEGRITY OF "different_pressure_data_source"
        for x in s.different_pressure_data_source:
            assert x.from_date <= x.to_date, (
                "from_date has to smaller than to_date " + f"({x.from_date} > {x.to_date})"
            )
        for i in range(len(s.different_pressure_data_source) - 1):
            x1, x2 = s.different_pressure_data_source[i : i + 2]
            expected_x2_from_date = (
                datetime.strptime(x1.to_date, "%Y%m%d") + timedelta(days=1)
            ).strftime("%Y%m%d")
            assert not (
                expected_x2_from_date > x2.from_date
            ), f"time periods are overlapping: {x1.dict()}, {x1.dict()}"

        # TEST INTEGRITY OF ADJACENT "utc_offset" ITEMS
        for o1, o2 in zip(s.utc_offsets[:-1], s.utc_offsets[1:]):
            assert (
                o1.utc_offset != o2.utc_offset
            ), "two neighboring date ranges should not have the same utc_offset"

        # TEST INTEGRITY OF ADJACENT "pressure_calibration_factors" ITEMS
        for p1, p2 in zip(s.pressure_calibration_factors[:-1], s.pressure_calibration_factors[1:]):
            assert (
                p1.factor != p2.factor
            ), "two neighboring date ranges should not have the same pressure calibration factor"

        # TEST INTEGRITY OF ADJACENT "locations" ITEMS
        for l1, l2 in zip(s.locations[:-1], s.locations[1:]):
            assert (
                l1.location_id != l2.location_id
            ), "two neighboring date ranges should not have the same location_id"
