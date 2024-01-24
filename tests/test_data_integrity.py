import datetime
import os
import json
import pytest
import em27_metadata

_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.mark.library
@pytest.mark.action
def test_data_integrity() -> None:
    location_data = em27_metadata.load_from_example_data()
    example_sensor_data_contexts_1 = location_data.get(
        sensor_id="sid1",
        from_datetime=datetime.datetime(
            2020, 8, 26, 0, 0, 0, tzinfo=datetime.timezone.utc
        ),
        to_datetime=datetime.datetime(
            2020, 8, 26, 23, 59, 59, tzinfo=datetime.timezone.utc
        ),
    )
    assert len(example_sensor_data_contexts_1) == 1
    example_list_str = json.dumps(
        [example_sensor_data_contexts_1[0].model_dump()],
        indent=2,
    ).replace("\n", "").replace("\t", "").replace(" ", "")
    with open(os.path.join(_PROJECT_DIR, "README.md")) as f:
        assert example_list_str in f.read().replace("\n", "").replace(
            "\t", ""
        ).replace(" ", "")
