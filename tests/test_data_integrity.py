import os
import json
from os.path import dirname
import pendulum

import pytest
from tum_esm_em27_metadata import interfaces, types

DATA_DIR = os.path.join(dirname(dirname(os.path.abspath(__file__))), "data")


@pytest.mark.ci
@pytest.mark.action
@pytest.mark.local
def test_data_integrity() -> None:
    with open(os.path.join(DATA_DIR, "locations.json")) as f:
        locations = [types.LocationMetadata(**l) for l in json.load(f)]

    with open(os.path.join(DATA_DIR, "sensors.json")) as f:
        sensors = [types.SensorMetadata(**l) for l in json.load(f)]

    with open(os.path.join(DATA_DIR, "campaigns.json")) as f:
        campaigns = [types.CampaignMetadata(**l) for l in json.load(f)]

    location_data = interfaces.EM27MetadataInterface(locations, sensors, campaigns)

    example_sensor = location_data.sensors[0]
    example_sensor_location = example_sensor.locations[0]

    date = example_sensor_location.from_datetime.to_rfc3339_string()[:10]  # type: ignore
    from_datetime = pendulum.parse(f"{date}T00:00:00+00:00")
    to_datetime = pendulum.parse(f"{date}T23:59:59+00:00")
    assert isinstance(from_datetime, pendulum.DateTime)
    assert isinstance(to_datetime, pendulum.DateTime)

    example_sensor_data_contexts = location_data.get(
        example_sensor.sensor_id, from_datetime, to_datetime
    )
    assert len(example_sensor_data_contexts) >= 1
    for sdc in example_sensor_data_contexts:
        assert sdc.location.location_id == example_sensor_location.location_id


@pytest.mark.ci
@pytest.mark.action
@pytest.mark.local
def test_getter_function() -> None:
    locations = [
        types.LocationMetadata(
            **{
                "location_id": "lid1",
                "details": "description of location 1",
                "lon": 10.5,
                "lat": 48.1,
                "alt": 500,
            }
        ),
        types.LocationMetadata(
            **{
                "location_id": "lid2",
                "details": "description of location 2",
                "lon": 11.3,
                "lat": 48.0,
                "alt": 600,
            }
        ),
    ]
    sensors = [
        types.SensorMetadata(
            **{
                "sensor_id": "sid1",
                "serial_number": 51,
                "different_utc_offsets": [
                    {
                        "from_datetime": "2020-02-01T02:00:00+00:00",
                        "to_datetime": "2020-02-01T15:59:59+00:00",
                        "utc_offset": 1,
                    },
                    {
                        "from_datetime": "2020-02-01T16:00:00+00:00",
                        "to_datetime": "2020-02-01T21:59:59+00:00",
                        "utc_offset": 2,
                    },
                ],
                "different_pressure_data_sources": [
                    {
                        "from_datetime": "2020-02-01T02:00:00+00:00",
                        "to_datetime": "2020-02-01T14:59:59+00:00",
                        "source": "src1",
                    },
                    {
                        "from_datetime": "2020-02-01T15:00:00+00:00",
                        "to_datetime": "2020-02-01T21:59:59+00:00",
                        "source": "src2",
                    },
                ],
                "different_pressure_calibration_factors": [
                    {
                        "from_datetime": "2020-02-01T02:00:00+00:00",
                        "to_datetime": "2020-02-01T13:59:59+00:00",
                        "factor": 1.001,
                    },
                    {
                        "from_datetime": "2020-02-01T14:00:00+00:00",
                        "to_datetime": "2020-02-01T21:59:59+00:00",
                        "factor": 1.002,
                    },
                ],
                "different_output_calibration_factors": [
                    {
                        "from_datetime": "2020-02-01T02:00:00+00:00",
                        "to_datetime": "2020-02-01T12:59:59+00:00",
                        "factors_xco2": [1.001, 0],
                        "factors_xch4": [1.002, 0],
                        "factors_xco": [1.003, 0],
                        "calibration_scheme": "Ohyama2021",
                    },
                    {
                        "from_datetime": "2020-02-01T13:00:00+00:00",
                        "to_datetime": "2020-02-01T21:59:59+00:00",
                        "factors_xco2": [1.004, 0],
                        "factors_xch4": [1.005, 0],
                        "factors_xco": [1.006, 0],
                        "calibration_scheme": "Ohyama2021",
                    },
                ],
                "locations": [
                    {
                        "from_datetime": "2020-02-01T01:00:00+00:00",
                        "to_datetime": "2020-02-01T11:59:59+00:00",
                        "location_id": "lid1",
                    },
                    {
                        "from_datetime": "2020-02-01T12:00:00+00:00",
                        "to_datetime": "2020-02-01T22:59:59+00:00",
                        "location_id": "lid2",
                    },
                ],
            }
        ),
    ]

    location_data = interfaces.EM27MetadataInterface(locations, sensors, campaigns=[])

    from_datetime = pendulum.parse("2020-02-01T00:00:00+00:00")
    to_datetime = pendulum.parse("2020-02-01T23:59:59+00:00")
    assert isinstance(from_datetime, pendulum.DateTime), "must be a datetime"
    assert isinstance(to_datetime, pendulum.DateTime), "must be a datetime"

    chunks = location_data.get("sid1", from_datetime, to_datetime)

    assert len(chunks) == 8

    # check that the chunks are sorted and consecutive
    for c1, c2 in zip(chunks[:-1], chunks[1:]):
        assert c1.to_datetime == c2.from_datetime.add(seconds=-1)

    # check correct timewise splitting
    assert chunks[0].from_datetime == pendulum.parse("2020-02-01T01:00:00+00:00")
    assert chunks[1].from_datetime == pendulum.parse("2020-02-01T02:00:00+00:00")
    assert chunks[2].from_datetime == pendulum.parse("2020-02-01T12:00:00+00:00")
    assert chunks[3].from_datetime == pendulum.parse("2020-02-01T13:00:00+00:00")
    assert chunks[4].from_datetime == pendulum.parse("2020-02-01T14:00:00+00:00")
    assert chunks[5].from_datetime == pendulum.parse("2020-02-01T15:00:00+00:00")
    assert chunks[6].from_datetime == pendulum.parse("2020-02-01T16:00:00+00:00")
    assert chunks[7].from_datetime == pendulum.parse("2020-02-01T22:00:00+00:00")

    # TODO: check values of utc offsets
    # TODO: check values of pressure data sources
    # TODO: check values of pressure calibration factors
    # TODO: check values of output calibration factors
    # TODO: check values of locations
