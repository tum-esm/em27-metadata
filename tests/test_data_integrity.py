import os
import json
from os.path import dirname

import pytest
from tum_esm_em27_metadata import interfaces, types

DATA_DIR = os.path.join(dirname(dirname(os.path.abspath(__file__))), "data")


@pytest.mark.ci
@pytest.mark.action
@pytest.mark.local
def test_data_integrity() -> None:
    with open(os.path.join(DATA_DIR, "locations.json")) as f:
        locations = [types.Location(**l) for l in json.load(f)]

    with open(os.path.join(DATA_DIR, "sensors.json")) as f:
        sensors = [types.Sensor(**l) for l in json.load(f)]

    with open(os.path.join(DATA_DIR, "campaigns.json")) as f:
        campaigns = [types.Campaign(**l) for l in json.load(f)]

    location_data = interfaces.EM27MetadataInterface(locations, sensors, campaigns)

    example_sensor = location_data.sensors[0]
    example_sensor_location = example_sensor.locations[0]
    example_sensor_data_context = location_data.get(
        example_sensor.sensor_id, example_sensor_location.from_date
    )
    assert example_sensor_data_context.location.location_id == example_sensor_location.location_id

    example_sensor_location = example_sensor.locations[0]
    example_sensor_data_context = location_data.get(
        example_sensor.sensor_id, example_sensor_location.from_date
    )
    assert example_sensor_data_context.location.location_id == example_sensor_location.location_id
