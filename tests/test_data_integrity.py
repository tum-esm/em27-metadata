import datetime
import os
import json
from os.path import dirname
import pytest
import em27_metadata

DATA_DIR = os.path.join(dirname(dirname(os.path.abspath(__file__))), "data")


@pytest.mark.ci
@pytest.mark.action
@pytest.mark.local
def test_data_integrity() -> None:
    with open(os.path.join(DATA_DIR, "locations.json")) as f:
        locations = [em27_metadata.types.LocationMetadata(**l) for l in json.load(f)]

    with open(os.path.join(DATA_DIR, "sensors.json")) as f:
        sensors = [em27_metadata.types.SensorMetadata(**l) for l in json.load(f)]

    with open(os.path.join(DATA_DIR, "campaigns.json")) as f:
        campaigns = [em27_metadata.types.CampaignMetadata(**l) for l in json.load(f)]

    location_data = em27_metadata.interfaces.EM27MetadataInterface(locations, sensors, campaigns)

    example_sensor = location_data.sensors[0]
    example_sensor_location = example_sensor.locations[0]

    date_string = example_sensor_location.from_datetime.strftime("%Y-%m-%d")
    from_datetime = datetime.datetime.fromisoformat(f"{date_string}T00:00:00+00:00")
    to_datetime = datetime.datetime.fromisoformat(f"{date_string}T23:59:59+00:00")

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
        em27_metadata.types.LocationMetadata(
            **{
                "location_id": "lid1",
                "details": "description of location 1",
                "lon": 10.5,
                "lat": 48.1,
                "alt": 500,
            }
        ),
        em27_metadata.types.LocationMetadata(
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
        em27_metadata.types.SensorMetadata(
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
                        "to_datetime": "2020-02-01T09:59:59+00:00",
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

    location_data = em27_metadata.interfaces.EM27MetadataInterface(locations, sensors, campaigns=[])

    from_datetime = datetime.datetime.fromisoformat("2020-02-01T00:00:00+00:00")
    to_datetime = datetime.datetime.fromisoformat("2020-02-01T23:59:59+00:00")

    chunks = location_data.get("sid1", from_datetime, to_datetime)

    assert len(chunks) == 8

    # check correct splitting

    from_datetimes = [c.from_datetime for c in chunks]
    assert from_datetimes == [
        datetime.datetime.fromisoformat("2020-02-01T01:00:00+00:00"),
        datetime.datetime.fromisoformat("2020-02-01T02:00:00+00:00"),
        datetime.datetime.fromisoformat("2020-02-01T12:00:00+00:00"),
        datetime.datetime.fromisoformat("2020-02-01T13:00:00+00:00"),
        datetime.datetime.fromisoformat("2020-02-01T14:00:00+00:00"),
        datetime.datetime.fromisoformat("2020-02-01T15:00:00+00:00"),
        datetime.datetime.fromisoformat("2020-02-01T16:00:00+00:00"),
        datetime.datetime.fromisoformat("2020-02-01T22:00:00+00:00"),
    ]
    to_datetimes = [c.to_datetime for c in chunks]
    assert to_datetimes == [
        datetime.datetime.fromisoformat("2020-02-01T01:59:59+00:00"),
        datetime.datetime.fromisoformat("2020-02-01T09:59:59+00:00"),
        datetime.datetime.fromisoformat("2020-02-01T12:59:59+00:00"),
        datetime.datetime.fromisoformat("2020-02-01T13:59:59+00:00"),
        datetime.datetime.fromisoformat("2020-02-01T14:59:59+00:00"),
        datetime.datetime.fromisoformat("2020-02-01T15:59:59+00:00"),
        datetime.datetime.fromisoformat("2020-02-01T21:59:59+00:00"),
        datetime.datetime.fromisoformat("2020-02-01T22:59:59+00:00"),
    ]

    utc_offsets = [c.utc_offset for c in chunks]
    assert utc_offsets == [0, 1, 1, 1, 1, 1, 2, 0]

    pressure_data_sources = [c.pressure_data_source for c in chunks]
    assert pressure_data_sources == ["sid1", "src1", "src1", "src1", "src1", "src2", "src2", "sid1"]

    pressure_calibration_factors = [c.pressure_calibration_factor for c in chunks]
    assert pressure_calibration_factors == [1.0, 1.001, 1.001, 1.001, 1.002, 1.002, 1.002, 1.0]

    output_calibration_factors = [c.output_calibration_factors_xco2[0] for c in chunks]
    assert output_calibration_factors == [1, 1.001, 1.001, 1.004, 1.004, 1.004, 1.004, 1]

    location_ids = [c.location.location_id for c in chunks]
    assert location_ids == ["lid1", "lid1", "lid2", "lid2", "lid2", "lid2", "lid2", "lid2"]
