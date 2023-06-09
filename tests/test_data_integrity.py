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
