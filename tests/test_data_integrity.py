import datetime
import os
import json
import pytest
import em27_metadata

DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"
)


@pytest.mark.library
@pytest.mark.action
def test_data_integrity() -> None:
    with open(os.path.join(DATA_DIR, "locations.json")) as f:
        locations = em27_metadata.types.LocationMetadata.model_validate_json(
            f.read()
        )

    with open(os.path.join(DATA_DIR, "sensors.json")) as f:
        sensors = em27_metadata.types.SensorMetadata.model_validate_json(
            f.read()
        )

    with open(os.path.join(DATA_DIR, "campaigns.json")) as f:
        campaigns = em27_metadata.types.CampaignMetadata.model_validate_json(
            f.read()
        )

    location_data = em27_metadata.interfaces.EM27MetadataInterface(
        locations, sensors, campaigns
    )

    example_sensor = location_data.sensors.root[0]
    example_sensor_setup = example_sensor.setups[0]

    date_string = example_sensor_setup.from_datetime.strftime("%Y-%m-%d")
    from_datetime = datetime.datetime.fromisoformat(
        f"{date_string}T00:00:00+00:00"
    )
    to_datetime = datetime.datetime.fromisoformat(
        f"{date_string}T23:59:59+00:00"
    )

    example_sensor_data_contexts = location_data.get(
        example_sensor.sensor_id, from_datetime, to_datetime
    )
    assert len(example_sensor_data_contexts) >= 1
    for sdc in example_sensor_data_contexts:
        assert sdc.location.location_id == example_sensor_setup.value.location_id
